""" DXFields
"""
from plone import api
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from plone.restapi.serializer.dxfields import DefaultPrimaryFieldTarget
from plone.namedfile.interfaces import INamedFileField
from zope.component import adapter
from zope.interface import implementer
from zope.schema.interfaces import IDatetime
from plone.app.dexterity.behaviors.metadata import IOwnership
from zope.schema.interfaces import ITuple
from zope.publisher.interfaces.browser import IBrowserRequest
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.interfaces import IFieldDeserializer
from plone.restapi.serializer.converters import json_compatible
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite
import copy

from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer
try:
    from eea.coremetadata.metadata import ICoreMetadata
except ImportError:
    # Fallback
    ICoreMetadata = IPublication


@implementer(IFieldSerializer)
@adapter(ITuple, IDexterityContent, Interface)
class CreatorsFieldSerializer(DefaultFieldSerializer):
    """Creators field serializer"""

    def __call__(self):
        value = copy.deepcopy(self.get_value())
        print('first value', value)

        if self.field is IOwnership["creators"]:
            fullnames = []
            for userid in value:
                user = api.user.get(userid)
                if user:
                    fullname = user.getProperty("fullname", "")
                    fullnames.append(fullname if fullname else userid)
                else:
                    fullnames.append(userid)

            value = fullnames
        return json_compatible(value)

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
        if value and self.field.interface in (IPublication, ICoreMetadata,):
            # the patch: we want the dates with full tz infos
            # default value is taken from
            # plone.app.dexterity.behaviors.metadata.Publication that escape
            # timezone
            return getattr(self.context, self.field.__name__)()
        return value


@adapter(INamedFileField, IDexterityContent, IEeaVoltoPolicyLayer)
class EEAPrimaryFileFieldTarget(DefaultPrimaryFieldTarget):
    """ EEAPrimaryFileFieldTarget adapter of PrimaryFileFieldTarget
    """
    def __call__(self):
        if self.field.__name__ == 'file':
            return
