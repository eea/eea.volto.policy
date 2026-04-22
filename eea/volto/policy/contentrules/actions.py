"""EEAContentTypes actions for plone.app.contentrules"""

import logging
from AccessControl import SpecialUsers, getSecurityManager
from AccessControl.SecurityManagement import (
    newSecurityManager,
    setSecurityManager,
)
from OFS.SimpleItem import SimpleItem
from plone.app.contentrules.browser.formhelper import (
    NullAddForm,
)
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope.component import adapter
from zope.interface import Interface, implementer

logger = logging.getLogger("eea.volto.policy")


class ISetPublicationDateToNullAction(Interface):
    """Set Publication Date to null"""


@implementer(ISetPublicationDateToNullAction, IRuleElementData)
class SetPublicationDateToNullAction(SimpleItem):
    """Set publication date to null action"""

    element = "eea.volto.policy.set_publication_date_to_null"
    summary = "I will set publication date to null"


@implementer(IExecutable)
@adapter(Interface, ISetPublicationDateToNullAction, Interface)
class SetPublicationDateToNullExecutor:
    """Set Publication Date to null executor"""

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        obj = self.event.object
        try:
            # Bypass user roles in order to rename old version
            oldSecurityManager = getSecurityManager()
            newSecurityManager(None, SpecialUsers.system)
            obj.setEffectiveDate(None)

            # Switch back to the current user
            setSecurityManager(oldSecurityManager)
        except Exception as err:
            logger.exception(err)
            return True
        return True


class SetPublicationDateToNullAddForm(NullAddForm):
    """Set Publication Date to null addform"""

    def create(self):
        """Create content-rule"""
        return SetPublicationDateToNullAction()
