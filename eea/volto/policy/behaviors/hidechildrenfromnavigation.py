"""Hide children from navigation behavior"""
from plone.app.dexterity import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from zope.interface import provider
from zope.schema import Bool


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
        description=_(
            "Check this to add a setting to hide the children from navigation"
        ),
        default=False,
        required=False
    )
