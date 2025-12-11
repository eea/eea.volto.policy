"""
Field inheritance utilities.

Provides functions to traverse the acquisition chain and find
field values from parent objects when the current object has none.
"""

from Acquisition import aq_base
from plone.registry.interfaces import IRegistry
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.schema import getFields
from zope.security import checkPermission
from zope.component import getUtility
from zope.interface.interfaces import ComponentLookupError

from eea.volto.policy.interfaces import IInheritableFieldsSettings


def get_inheritable_fields():
    """Get list of field names configured for inheritance."""
    try:
        registry = getUtility(IRegistry)
        settings = registry.forInterface(
            IInheritableFieldsSettings,
            prefix="eea.volto.policy.inheritable_fields",
            check=False
        )
        return settings.inheritable_fields or []
    except (KeyError, ComponentLookupError):
        return []


def get_inherited_field_value(context, field_name):
    """
    Traverse aq_chain to find first ancestor with a value for field_name.

    Starts from the context and walks up the acquisition chain until
    it finds an object with the specified field set or reaches the site root.

    Returns:
        tuple: (field_value, source_obj) where source_obj is None if it's local
    """
    for obj in context.aq_chain:
        # Stop at site root
        if IPloneSiteRoot.providedBy(obj):
            break

        # Only check Dexterity content
        if not IDexterityContent.providedBy(obj):
            continue

        # Security check - ensure user can view the object
        if not checkPermission("zope2.View", obj):
            break

        # Check if this object has the field in any of its schemas
        for schema in iterSchemata(obj):
            fields = getFields(schema)
            if field_name in fields:
                # Use aq_base to check the raw attribute without acquisition
                value = getattr(aq_base(obj), field_name, None)
                if value:
                    # Return (value, None) if it's the context itself (local)
                    # Return (value, source_obj) if inherited from parent
                    is_local = obj is context
                    return (value, None if is_local else obj)

    return (None, None)
