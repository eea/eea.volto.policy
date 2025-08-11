"""Fix wrong url after migrations, with resume support"""

import logging
import re
import transaction

from Acquisition import aq_base
from Products.Five import BrowserView
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import iterSchemata
from zope.schema import getFields
from zope.component import ComponentLookupError
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError

logger = logging.getLogger(__name__)

# Registry key to store progress
REGISTRY_KEY = "eea.volto.policy.internal_api_path.last_processed_index"


class UpdateInternalApiPathView(BrowserView):
    """Browser view to replace backend URLs with relative paths only,
    with resume support"""

    def get_search_strings(self):
        registry_urls = api.portal.get_registry_record(
            "eea.volto.policy.internal_api_path.replacement_urls"
        )
        return list(registry_urls) if registry_urls else []

    def get_last_processed_index(self):
        try:
            last = api.portal.get_registry_record(REGISTRY_KEY)
            if isinstance(last, int) and last >= 0:
                return last
        except Exception:
            pass
        return 0

    def set_last_processed_index(self, index):
        try:
            api.portal.set_registry_record(REGISTRY_KEY, index)
        except Exception as e:
            logger.error("Could not save last processed index: %s", str(e))

    def __call__(self):
        return self.update_content()

    def update_content(self):
        try:
            portal = self.context.portal_url.getPortalObject()
            catalog = portal.portal_catalog
            brains = catalog()
            total = len(brains)
            logger.info("Found %d content items in catalog", total)
        except (AttributeError, ComponentLookupError) as e:
            logger.error("Error accessing catalog: %s", str(e))
            return "Could not access portal catalog"

        batch_size = 10
        start_index = self.get_last_processed_index()
        logger.info("Starting at index %d", start_index)

        if start_index >= total:
            return "All items have been processed."

        modified = []

        # Process only next batch
        end_index = min(start_index + batch_size, total)
        batch = brains[start_index:end_index]

        for offset, brain in enumerate(batch, start=start_index):
            try:
                obj = brain.getObject()
                if self.process_object(obj):
                    obj.reindexObject()
                    modified.append(obj.absolute_url())
            except (AttributeError, ConflictError, Unauthorized) as e:
                logger.error(
                    "Error processing %s: %s", brain.getPath(), str(e)
                )
            self.set_last_processed_index(offset + 1)  # save progress after each item

        transaction.commit()

        output = "=" * 80 + "\n"
        output += f"URL REPLACEMENT PROCESS PROGRESS\nProcessed items {start_index + 1} to {end_index} of {total}\n"
        output += "=" * 80 + "\n\n"
        output += f"Items modified in this run: {len(modified)}\n\n"

        if modified:
            output += "MODIFIED PAGES:\n"
            for i, url in enumerate(modified, 1):
                output += f"   {i:2d}. {url}\n"
        else:
            output += "No items were modified in this run.\n"

        if end_index >= total:
            output += "\nProcessing complete! Resetting last processed index.\n"
            self.set_last_processed_index(0)  # reset for next full run

        output += "\n" + "=" * 80
        return output

    def process_object(self, obj):
        changed = False

        if hasattr(aq_base(obj), "blocks"):
            try:
                blocks = obj.blocks
                new_blocks, blocks_changed = self.process_value(blocks)
                if blocks_changed:
                    obj.blocks = new_blocks
                    changed = True
            except (AttributeError, KeyError, TypeError) as e:
                logger.error(
                    "Error processing blocks on %s: %s",
                    obj.absolute_url(),
                    str(e),
                )

        try:
            for schema in iterSchemata(obj):
                for field_name, field in getFields(schema).items():
                    changed |= self.process_field(obj, field_name)
        except TypeError:
            if hasattr(aq_base(obj), "Schema"):
                schema = obj.Schema()
                for field in schema.fields():
                    field_name = field.getName()
                    try:
                        value = field.get(obj)
                        new_value, was_changed = self.process_value(value)
                        if was_changed:
                            field.set(obj, new_value)
                            changed = True
                    except (AttributeError, KeyError, ValueError) as e:
                        logger.error(
                            "Error processing Archetypes field %s on %s: %s",
                            field_name,
                            obj.absolute_url(),
                            str(e),
                        )

        return changed

    def process_field(self, obj, field_name):
        if not hasattr(aq_base(obj), field_name):
            return False

        try:
            value = getattr(obj, field_name)
            if (callable(value) or
                    field_name.startswith("_") or
                    field_name.startswith("aq_")):
                return False

            new_value, was_changed = self.process_value(value)
            if was_changed:
                setattr(obj, field_name, new_value)
                return True
        except (AttributeError, KeyError, ValueError) as e:
            logger.error(
                "Error processing field %s on %s: %s",
                field_name,
                obj.absolute_url(),
                str(e),
            )

        return False

    def process_value(self, value):
        if isinstance(value, str):
            new_value = self.replace_urls(value)
            return new_value, new_value != value

        if isinstance(value, RichTextValue):
            new_raw = self.replace_urls(value.raw)
            if new_raw != value.raw:
                return (
                    RichTextValue(
                        raw=new_raw,
                        mimeType=value.mimeType,
                        outputMimeType=value.outputMimeType,
                        encoding=value.encoding,
                    ),
                    True,
                )
            return value, False

        if isinstance(value, dict):
            new_dict = {}
            any_changed = False
            for k, v in value.items():
                new_v, item_changed = self.process_value(v)
                new_dict[k] = new_v
                any_changed |= item_changed
            return new_dict, any_changed

        if isinstance(value, list):
            new_list = []
            any_changed = False
            for item in value:
                new_item, item_changed = self.process_value(item)
                new_list.append(new_item)
                any_changed |= item_changed
            return new_list, any_changed

        return value, False

    def replace_urls(self, text):
        if not isinstance(text, str):
            return text

        search_strings = self.get_search_strings()
        if not any(s in text for s in search_strings):
            return text

        REPLACE_PATTERN = re.compile(
            rf"(?:{'|'.join(re.escape(s) for s in search_strings)})[^\s\"'>]+"
        )

        def replace_match(match):
            url = match.group(0)
            base = next(
                (s for s in search_strings if url.startswith(s)),
                None,
            )

            if not base:
                return url

            relative_path = url.replace(base, "", 1)
            path = "/" + relative_path.lstrip("/")
            return path

        return REPLACE_PATTERN.sub(replace_match, text)
