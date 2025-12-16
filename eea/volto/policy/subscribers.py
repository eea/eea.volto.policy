"""
Event subscribers for field inheritance.

Handles reindexing of descendants when inheritable fields change on a parent.
"""

import logging
from Acquisition import aq_base
from plone import api
from plone.dexterity.interfaces import IDexterityContent
from zope.lifecycleevent.interfaces import IAttributes

from eea.volto.policy.inherit import get_inheritable_fields

logger = logging.getLogger(__name__)


def get_modified_field_names(event):
    """Extract field names from modification event descriptions.

    Field names may come as 'IInterface.field_name' or just 'field_name'.
    We normalize to just the field name.
    """
    modified = set()
    for desc in event.descriptions or []:
        if IAttributes.providedBy(desc):
            for attr in desc.attributes or []:
                # Strip interface prefix if present
                # (e.g., 'IPreview.preview_image' -> 'preview_image')
                field_name = attr.split(".")[-1] if "." in attr else attr
                modified.add(field_name)
    return modified


def reindex_inheriting_descendants(obj, field_names):
    """
    Find and reindex descendants that inherit any of the specified fields.

    Only reindexes objects that don't have their own value for at least
    one of the fields, meaning they would inherit from this object.
    """
    catalog = api.portal.get_tool("portal_catalog")
    path = "/".join(obj.getPhysicalPath())

    brains = catalog.unrestrictedSearchResults(
        path={"query": path, "depth": -1})

    reindexed = 0
    for brain in brains:
        if brain.getPath() == path:
            continue  # Skip self

        try:
            child = brain._unrestrictedGetObject()
        except (KeyError, AttributeError):
            continue

        if not IDexterityContent.providedBy(child):
            continue

        # Check if child inherits any of the modified fields
        inherits_any = False
        for field_name in field_names:
            if not getattr(aq_base(child), field_name, None):
                inherits_any = True
                break

        if inherits_any:
            child.reindexObject()
            reindexed += 1

    if reindexed:
        logger.info(
            "Reindexed %d descendants of %s (inheritable fields changed: %s)",
            reindexed,
            path,
            ", ".join(field_names),
        )


def on_content_modified(obj, event):
    """
    Reindex descendants when an inheritable field changes.

    Listens for IObjectModifiedEvent and checks if any of the modified
    fields are configured as inheritable. If so, finds all descendants
    that would inherit from this object and reindexes them.
    """
    if not IDexterityContent.providedBy(obj):
        return

    inheritable_fields = get_inheritable_fields()
    if not inheritable_fields:
        return

    # Get which fields were actually modified
    modified_fields = get_modified_field_names(event)

    # Determine which inheritable fields were modified
    if modified_fields:
        fields_to_check = modified_fields & set(inheritable_fields)
    else:
        # No descriptions - check all inheritable fields that have values
        fields_to_check = set(inheritable_fields)

    if not fields_to_check:
        return

    # Filter to fields that actually have values on this object
    fields_with_values = {
        name for name in fields_to_check if getattr(aq_base(obj), name, None)
    }

    if fields_with_values:
        reindex_inheriting_descendants(obj, fields_with_values)
