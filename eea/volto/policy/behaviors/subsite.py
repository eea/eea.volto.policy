"""EEA-specific Subsite behavior."""

from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope.interface import provider
from zope.schema import Bool

from eea.volto.policy import EEAMessageFactory as _


@provider(IFormFieldProvider)
class ISubsiteLogoMain(model.Schema):
    """Allow the Subsite logo to replace the EEA logo in the header."""

    subsite_logo_main = Bool(
        title=_("Use as main logo"),
        description=_("Replace the EEA logo in the site header with the subsite logo."),
        required=False,
        default=False,
    )
