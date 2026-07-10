"""DXFields serializers with inheritance support."""

from plone.app.dexterity.behaviors.metadata import IPublication
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.interfaces import INamedFileField
from plone.namedfile.interfaces import INamedImageField
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from plone.restapi.serializer.dxfields import DefaultPrimaryFieldTarget
from plone.restapi.serializer.dxfields import ImageFieldSerializer
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IDatetime
from zope.schema.interfaces import IField

from eea.coremetadata.interfaces import IGeoCoverageField
from eea.geolocation.grouping import serialize_grouped_geolocation
from eea.volto.policy.inherit import InheritableMixin
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer

try:
    from eea.coremetadata.metadata import ICoreMetadata
except ImportError:
    ICoreMetadata = IPublication

try:
    from collective.exportimport.interfaces import IBase64BlobsMarker
    from collective.exportimport.interfaces import IPathBlobsMarker
    from collective.exportimport.serializer import ImageFieldSerializerWithBlobs
    from collective.exportimport.serializer import (
        ImageFieldSerializerWithBlobPaths,
    )

    HAS_EXPORTIMPORT = True
except ImportError:
    HAS_EXPORTIMPORT = False


# Generic inheritance-aware serializers


@implementer(IFieldSerializer)
@adapter(INamedImageField, IDexterityContent, IEeaVoltoPolicyLayer)
class InheritableImageFieldSerializer(InheritableMixin, ImageFieldSerializer):
    """
    Image field serializer with inheritance support.

    This registration is more specific than collective.exportimport's
    request-marker based serializers, so it would shadow them and image
    blobs would be exported as download urls instead of base64/blob-paths.
    Defer to them when an export marker is on the request.
    """

    def __call__(self):
        if HAS_EXPORTIMPORT:
            if IBase64BlobsMarker.providedBy(self.request):
                return ImageFieldSerializerWithBlobs(
                    self.field, self.context, self.request
                )()
            if IPathBlobsMarker.providedBy(self.request):
                return ImageFieldSerializerWithBlobPaths(
                    self.field, self.context, self.request
                )()
        return super().__call__()


@implementer(IFieldSerializer)
@adapter(IField, IDexterityContent, IEeaVoltoPolicyLayer)
class InheritableFieldSerializer(InheritableMixin, DefaultFieldSerializer):
    """
    Generic field serializer with inheritance support.
    """


@implementer(IFieldSerializer)
@adapter(IGeoCoverageField, IDexterityContent, IEeaVoltoPolicyLayer)
class GeoCoverageFieldSerializer(InheritableMixin, DefaultFieldSerializer):
    """Geo coverage field serializer with grouping and inheritance support."""

    def __call__(self):
        value = super().__call__()

        if isinstance(value, dict):
            value = serialize_grouped_geolocation(
                value,
                context=self.context,
            )

        return value


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
