"""Side navigation behaviors"""

from plone.app.dexterity import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider
from zope.schema import TextLine


@provider(IFormFieldProvider)
class IEEASideNavTitle(model.Schema):
    """Behavior interface to set a title for the side navigation."""

    side_nav_title = TextLine(title=_("Side Navigation title"), required=False)
