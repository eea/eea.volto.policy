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

from eea.volto.policy.inherit import InheritableMixin
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer

try:
    from eea.coremetadata.metadata import ICoreMetadata
except ImportError:
    ICoreMetadata = IPublication


# Generic inheritance-aware serializers


@implementer(IFieldSerializer)
@adapter(INamedImageField, IDexterityContent, IEeaVoltoPolicyLayer)
class InheritableImageFieldSerializer(InheritableMixin, ImageFieldSerializer):
    """
    Image field serializer with inheritance support.
    """


@implementer(IFieldSerializer)
@adapter(IField, IDexterityContent, IEeaVoltoPolicyLayer)
class InheritableFieldSerializer(InheritableMixin, DefaultFieldSerializer):
    """
    Generic field serializer with inheritance support.
    """

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
