"""Side navigation behaviors"""
from plone.app.dexterity import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from zope.interface import provider
from zope.schema import TextLine
from zope.schema import Bool


@provider(IFormFieldProvider)
class IEEASideNavTitle(model.Schema):
    """Behavior interface to set a title for the side navigation."""

    side_nav_title = TextLine(title=_("Side Navigation title"), required=False)


@provider(IFormFieldProvider)
class IEEAHideChildrenFromNavigation(model.Schema):
    """Behavior interface to hide children from navigation."""

    fieldset(
        'settings',
        label=_('Settings'),
        fields=['hideChildrenFromNavigation']
    )

    hideChildrenFromNavigation = Bool(
        title=_("Hide Children From Navigation"),
        description=_("Check this to hide child items from appearing in navigation menus"),
        default=False,
        required=False
    )
