"""DXFields serializers with inheritance support."""

from Acquisition import aq_base
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.interfaces import INamedFileField
from plone.namedfile.interfaces import INamedImageField
from plone.restapi.imaging import get_original_image_url
from plone.restapi.imaging import get_scales
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from plone.restapi.serializer.dxfields import DefaultPrimaryFieldTarget
from plone.restapi.serializer.dxfields import ImageFieldSerializer
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IDatetime
from zope.schema.interfaces import IField

from eea.volto.policy.inherit import (
    get_inheritable_fields,
    get_inherited_field_value,
)
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer

try:
    from eea.coremetadata.metadata import ICoreMetadata
except ImportError:
    ICoreMetadata = IPublication


# Generic inheritance-aware serializers

@implementer(IFieldSerializer)
@adapter(INamedImageField, IDexterityContent, IEeaVoltoPolicyLayer)
class InheritableImageFieldSerializer(ImageFieldSerializer):
    """
    Image field serializer with inheritance support.

    If local image exists, uses Plone's default serialization.
    If no local image and field is inheritable, gets from ancestor.
    """

    def __call__(self):
        # Check for local image first
        if self.field.get(self.context):
            return super().__call__()

        # No local image - check if field is inheritable
        field_name = self.field.__name__
        if field_name not in get_inheritable_fields():
            return None

        # Get inherited value
        image, source_obj = get_inherited_field_value(self.context, field_name)
        if not image or not source_obj:
            return None

        # Serialize inherited image using source object
        width, height = image.getImageSize()
        url = get_original_image_url(source_obj, field_name, width, height)

        if width != -1 and height != -1:
            scales = get_scales(source_obj, self.field, width, height)
        else:
            scales = {}

        result = {
            "filename": image.filename,
            "content-type": image.contentType,
            "size": image.getSize(),
            "download": url,
            "width": width,
            "height": height,
            "scales": scales,
            "inherited_from": {
                "@id": source_obj.absolute_url(),
                "title": source_obj.title,
            },
        }
        return json_compatible(result)


@implementer(IFieldSerializer)
@adapter(IField, IDexterityContent, IEeaVoltoPolicyLayer)
class InheritableFieldSerializer(DefaultFieldSerializer):
    """
    Generic field serializer with inheritance support.

    Works for any field type (text, etc). If local value exists,
    uses default serialization. If no local value and field is
    inheritable, gets from ancestor.
    """

    def __call__(self):
        # Check for local value first
        local_value = getattr(aq_base(self.context), self.field.__name__, None)
        if local_value is not None:
            return super().__call__()

        # No local value - check if field is inheritable
        field_name = self.field.__name__
        if field_name not in get_inheritable_fields():
            return super().__call__()

        # Get inherited value
        value, source_obj = get_inherited_field_value(self.context, field_name)
        if value is None or source_obj is None:
            return None

        return json_compatible(value)


# Other serializers

@adapter(IDatetime, IDexterityContent, IEeaVoltoPolicyLayer)
@implementer(IFieldSerializer)
class DateTimeFieldSerializer(DefaultFieldSerializer):
    """DateTimeFieldSerializer with timezone support."""

    def get_value(self, default=None):
        value = getattr(
            self.field.interface(self.context), self.field.__name__, default
        )
        if value and self.field.interface in (IPublication, ICoreMetadata):
            return getattr(self.context, self.field.__name__)()
        return value


@adapter(INamedFileField, IDexterityContent, IEeaVoltoPolicyLayer)
class EEAPrimaryFileFieldTarget(DefaultPrimaryFieldTarget):
    """EEAPrimaryFileFieldTarget adapter."""

    def __call__(self):
        if self.field.__name__ == "file":
            return
