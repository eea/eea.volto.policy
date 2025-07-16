# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from plone.dexterity.utils import iterSchemata
from zope.schema import getFields
from plone.app.textfield.value import RichTextValue
import logging
import transaction
import re
from Acquisition import aq_base

logger = logging.getLogger(__name__)

SEARCH_STRING = "http://backend:8080"
REPLACE_PATTERN = re.compile(rf"{re.escape(SEARCH_STRING)}[^\s\"'>]+")

class UpdateInternalApiPathView(BrowserView):
    """Browser view to replace backend URLs with resolveuid references"""

    def __call__(self):
        return self.update_content()

    def update_content(self):
        try:
            portal = self.context.portal_url.getPortalObject()
            catalog = portal.portal_catalog
            brains = catalog()
            logger.info(f"Found {len(brains)} content items in catalog")
        except Exception as e:
            logger.error(f"Error accessing catalog: {str(e)}")
            return "Could not access portal catalog"

        # Build path to UID mapping
        path_to_uid = {}
        for brain in brains:
            try:
                path = brain.getPath()
                path_to_uid[path] = brain.UID
                if path.startswith('/'):
                    path_to_uid[path[1:]] = brain.UID
            except Exception as e:
                logger.error(f"Error processing brain {brain.getPath()}: {str(e)}")

        logger.info(f"Created UID mapping for {len(path_to_uid)} paths")
        modified = []

        for brain in brains:
            try:
                obj = brain.getObject()
                if self.process_object(obj, path_to_uid):
                    obj.reindexObject()
                    modified.append(obj.absolute_url())
            except Exception as e:
                logger.error(f"Error processing {brain.getPath()}: {str(e)}")
                continue

        transaction.commit()
        msg = f"Updated {len(modified)} items. Modified content: {', '.join(modified)}"
        logger.info(msg)
        return msg

    def process_object(self, obj, path_to_uid):
        """Process all relevant fields in an object recursively"""
        changed = False

        # Process blocks field separately
        if hasattr(aq_base(obj), 'blocks'):
            try:
                blocks = obj.blocks
                new_blocks, blocks_changed = self.process_value(blocks, path_to_uid)
                if blocks_changed:
                    obj.blocks = new_blocks
                    changed = True
            except Exception as e:
                logger.error(f"Error processing blocks on {obj.absolute_url()}: {str(e)}")

        # Process Dexterity fields
        try:
            for schema in iterSchemata(obj):
                for field_name, field in getFields(schema).items():
                    changed |= self.process_field(obj, field_name, path_to_uid)
        except TypeError:
            if hasattr(aq_base(obj), 'Schema'):
                schema = obj.Schema()
                for field in schema.fields():
                    field_name = field.getName()
                    try:
                        value = field.get(obj)
                        new_value, was_changed = self.process_value(value, path_to_uid)
                        if was_changed:
                            field.set(obj, new_value)
                            changed = True
                    except Exception as e:
                        logger.error(f"Error processing Archetypes field {field_name} on {obj.absolute_url()}: {str(e)}")

        return changed

    def process_field(self, obj, field_name, path_to_uid):
        """Process a single field on an object"""
        if not hasattr(aq_base(obj), field_name):
            return False

        try:
            value = getattr(obj, field_name)
            # Skip methods and special attributes
            if callable(value) or field_name.startswith('_') or field_name.startswith('aq_'):
                return False
            new_value, was_changed = self.process_value(value, path_to_uid)
            
            if was_changed:

                setattr(obj, field_name, new_value)
                return True
        except Exception as e:
            logger.error(f"Error processing field {field_name} on {obj.absolute_url()}: {str(e)}")
        return False

    def process_value(self, value, path_to_uid):
        """Recursively process any value and replace URLs"""
        # Handle strings
        if isinstance(value, str):
            new_value = self.replace_urls(value, path_to_uid)
            return new_value, (new_value != value)
        
        # Handle rich text values
        elif isinstance(value, RichTextValue):
            new_raw = self.replace_urls(value.raw, path_to_uid)
            if new_raw != value.raw:
                return RichTextValue(
                    raw=new_raw,
                    mimeType=value.mimeType,
                    outputMimeType=value.outputMimeType,
                    encoding=value.encoding
                ), True
            return value, False
        
        # Handle dictionaries
        elif isinstance(value, dict):
            new_dict = {}
            any_changed = False
            for k, v in value.items():
                new_v, item_changed = self.process_value(v, path_to_uid)
                new_dict[k] = new_v
                any_changed = any_changed or item_changed
            return new_dict, any_changed
        
        # Handle lists
        elif isinstance(value, list):
            new_list = []
            any_changed = False
            for item in value:
                new_item, item_changed = self.process_value(item, path_to_uid)
                new_list.append(new_item)
                any_changed = any_changed or item_changed
            return new_list, any_changed
        
        return value, False

    def replace_urls(self, text, path_to_uid):
        """Replace backend URLs with resolveuid references"""
        if not isinstance(text, str) or SEARCH_STRING not in text:
            return text
                
        def replace_match(match):
            url = match.group(0)
            relative_path = url.replace(SEARCH_STRING, "", 1).lstrip('/')
            
            if not relative_path:
                return url
            sorted_paths = sorted(path_to_uid.keys(), key=len, reverse=True)
            for content_path in sorted_paths:
                norm_content_path = content_path.strip('/')
                norm_relative_path = relative_path.strip('/')
                if not norm_content_path:
                    continue
                if  norm_relative_path  in norm_content_path :
                    extra = norm_relative_path[len(norm_content_path):].lstrip('/')
                    uid = path_to_uid[content_path]
                    if extra:
                        return f"/resolveuid/{uid}/{extra}"
                    return f"/resolveuid/{uid}"
            
            # Log if no match found
            logger.warning(f"No UID found for path: {relative_path}")
            return url
        
        return REPLACE_PATTERN.sub(replace_match, text)