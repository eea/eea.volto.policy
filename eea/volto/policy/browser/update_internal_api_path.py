"""Fix wrong url after migrations"""

# pylint: disable=line-too-long

import logging
import re
from urllib.parse import urlparse
import transaction

from Acquisition import aq_base
from Products.Five import BrowserView
from plone import api
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import iterSchemata
from plone.restapi.deserializer.utils import path2uid
from zope.schema import getFields
from zope.component import ComponentLookupError
from zExceptions import Unauthorized
from ZODB.POSException import ConflictError

logger = logging.getLogger(__name__)


class UpdateInternalApiPathView(BrowserView):
    """Browser view to replace backend URLs with resolveuid references"""

    def get_search_strings(self):
        """Get URLs from registry configuration"""
        registry_urls = api.portal.get_registry_record(
            "eea.volto.policy.internal_api_path.replacement_urls"
        )
        return list(registry_urls) if registry_urls else []

    def __call__(self):
        return self.update_content()

    def update_content(self):
        """Main function that iterates through all objects in the catalog"""
        try:
            portal = self.context.portal_url.getPortalObject()
            catalog = portal.portal_catalog
            brains = catalog()
            logger.info("Found %d content items in catalog", len(brains))

        except (AttributeError, ComponentLookupError) as e:
            logger.error("Error accessing catalog: %s", str(e))
            return "Could not access portal catalog"

        modified = []

        for brain in brains:
            try:
                obj = brain.getObject()
                if self.process_object(obj):
                    obj.reindexObject()
                    modified.append(obj.absolute_url())
            except (AttributeError, ConflictError, Unauthorized) as e:
                logger.error(
                    "Error processing %s: %s", brain.getPath(), str(e)
                )

        transaction.commit()

        # Format output for display
        output = "=" * 80 + "\n"
        output += "URL REPLACEMENT PROCESS COMPLETED\n"
        output += "=" * 80 + "\n\n"
        output += "STATISTICS:\n"
        output += f"   • Total items processed: {len(brains)}\n"
        output += f"   • Items modified: {len(modified)}\n\n"

        if modified:
            output += "MODIFIED PAGES:\n"
            for i, url in enumerate(modified, 1):
                output += f"   {i:2d}. {url}\n"
        else:
            output += "No items were modified.\n"

        output += "\n" + "=" * 80
        return output

    def process_object(self, obj):
        """Process all relevant fields in an object recursively"""
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
        """Process a single field on an object"""
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
        """Recursively process any value and replace URLs"""
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
        """Replace backend URLs with resolveuid"""
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

            uid = path2uid(context=self.context, link=path)

            if uid and uid != path:
                return uid

            logger.warning("No UID found for path: %s", relative_path)
            return relative_path

        return REPLACE_PATTERN.sub(replace_match, text)
