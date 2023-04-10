""" DXFields
"""
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IDatetime


@adapter(IDatetime, IDexterityContent, IEeaVoltoPolicyLayer)
@implementer(IFieldSerializer)
class DateTimeFieldSerializer:
    """ DateTimeFieldSerializer
    """
    def __init__(self, field, context, request):
        self.context = context
        self.request = request
        self.field = field

    def __call__(self):
        return json_compatible(self.get_value())

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
