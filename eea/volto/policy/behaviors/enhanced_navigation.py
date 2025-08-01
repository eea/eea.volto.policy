"""Enhanced Navigation behaviors"""
from plone.app.dexterity import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
try:
    from plone.app.multilingual.interfaces import ILanguageIndependentField
except ImportError:
    ILanguageIndependentField = None

from zope.interface import provider
from zope.schema import Text


@provider(IFormFieldProvider)
class IEnhancedNavigationBehavior(model.Schema):
    """Behavior interface for Enhanced Navigation settings."""

    navigation_settings = Text(
        title=_("Navigation Settings"),
        description=_(
            "JSON object containing navigation settings for all menu routes"
        ),
        required=False,
        default="{}",
    )

    # Make field language independent
    if ILanguageIndependentField:
        model.directives.languageindependent('navigation_settings')
