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
            check=False,
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


class InheritableMixin:
    """Mixin that adds field inheritance support to any serializer."""

    @property
    def _base_serializer_class(self):
        """Get the base serializer class (the non-mixin parent)."""
        for base in self.__class__.__bases__:
            if base is not InheritableMixin:
                return base
        raise TypeError(
            "InheritableMixin must be used with a serializer base class")

    def _is_inheritable_field(self, field_name):
        """Check if field is inheritable, with request-level caching."""
        cache = getattr(self.request, "_v_inheritable_fields", None)
        if cache is None:
            cache = set(get_inheritable_fields())
            self.request._v_inheritable_fields = cache
        return field_name in cache

    def __call__(self):
        # Check for local value first
        if self.field.get(self.context):
            return super().__call__()

        # No local value - check if field is inheritable
        field_name = self.field.__name__
        if not self._is_inheritable_field(field_name):
            return super().__call__()

        # Get inherited value
        value, source_obj = get_inherited_field_value(self.context, field_name)
        if not value or source_obj is None:
            return super().__call__()

        # Use base serializer with inherited context
        return self._base_serializer_class(
            self.field, source_obj, self.request
        )()


def indexer_with_inheritance(indexer, obj, field_names, validator=None):
    if not indexer:
        raise TypeError(
            "indexer_with_inheritance must be used with an indexer")

    value = None

    try:
        value = indexer(obj)()
    except Exception:
        pass

    if value:
        return value

    inheritable_fields = get_inheritable_fields()

    for field_name in field_names:
        if field_name not in inheritable_fields:
            continue
        value, source_obj = get_inherited_field_value(obj, field_name)
        if source_obj:
            if validator and not validator(field_name, value):
                continue
            v = None
            try:
                v = indexer(source_obj)()
            except Exception:
                pass
            if v:
                value = v
                break

    return value
