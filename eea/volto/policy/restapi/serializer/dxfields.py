""" DXFields
"""
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IDatetime


@adapter(IDatetime, IDexterityContent, IEeaVoltoPolicyLayer)
@implementer(IFieldSerializer)
class DateTimeFieldSerializer(DefaultFieldSerializer):
    """ DateTimeFieldSerializer
    """
    def get_value(self, default=None):
        """ Get value
        """
        value = getattr(
            self.field.interface(self.context), self.field.__name__, default
        )
        if value and self.field.interface == IPublication:
            # the patch: we want the dates with full tz infos
            # default value is taken from
            # plone.app.dexterity.behaviors.metadata.Publication that escape
            # timezone
            return getattr(self.context, self.field.__name__)()
        return value
