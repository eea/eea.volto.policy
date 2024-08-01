from plone.app.dexterity import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


class IExcludeFromSiteNavigationDefault(Interface):
    def __call__():
        """boolean if item is by default excluded from site navigation or not."""


@implementer(IExcludeFromSiteNavigationDefault)
def default_exclude_false(context):
    """provide a default adapter with the standard uses"""
    return False


@implementer(IExcludeFromSiteNavigationDefault)
def default_exclude_true(context):
    """provide a alternative adapter with opposite default as standard"""
    return True


@provider(IContextAwareDefaultFactory)
def default_exclude(context):
    return IExcludeFromSiteNavigationDefault(context)


@provider(IFormFieldProvider)
class IExcludeFromSiteNavigation(model.Schema):
    """Behavior interface to exclude items from site navigation."""

    model.fieldset(
        "settings", label=_("Settings"), fields=["exclude_from_site_nav"]
    )

    exclude_from_site_nav = schema.Bool(
        title=_(
            "label_exclude_from_site_nav",
            default="Exclude from site navigation",
        ),
        description=_(
            "help_exclude_from_site_nav",
            default="If selected, this item will not appear in the "
            "Site navigation",
        ),
        defaultFactory=default_exclude,
        required=False,
    )

    directives.omitted("exclude_from_site_nav")
    directives.no_omit(IEditForm, "exclude_from_site_nav")
    directives.no_omit(IAddForm, "exclude_from_site_nav")
