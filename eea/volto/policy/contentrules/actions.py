""" EEAContentTypes actions for plone.app.contentrules
"""

import logging
from time import time

from AccessControl import SpecialUsers, getSecurityManager
from AccessControl.SecurityManagement import (
    newSecurityManager,
    setSecurityManager,
)
from DateTime import DateTime
from OFS.SimpleItem import SimpleItem
from plone import api
from plone.app.contentrules.browser.formhelper import (
    AddForm,
    EditForm,
    NullAddForm,
)
from plone.contentrules.rule.interfaces import IExecutable, IRuleElementData
from zope import schema
from zope.component import adapter
from zope.interface import Interface, implementer

logger = logging.getLogger("eea.dexterity.indicators")


class IRetractAndRenameOldVersionAction(Interface):
    """Retract and rename old version"""


@implementer(IRetractAndRenameOldVersionAction, IRuleElementData)
class RetractAndRenameOldVersionAction(SimpleItem):
    """Retract and rename old version action"""

    element = "eea.dexterity.indicators.retract_and_rename_old_version"
    summary = (
        "Will retract and rename older version of this Indicator. "
        "Then rename current Indicator (remove copy_of_ from id)"
    )


@implementer(IExecutable)
@adapter(Interface, IRetractAndRenameOldVersionAction, Interface)
class RetractAndRenameOldVersionExecutor(object):
    """Retract and rename old version executor"""

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        obj = self.event.object
        oid = obj.getId()
        parent = obj.getParentNode()

        old_id = new_id = None
        if oid.startswith("copy_of_"):
            old_id = oid.replace("copy_of_", "", 1)
            new_id = old_id + "-%d" % time()
        elif oid.endswith(".1"):
            old_id = oid.replace(".1", "", 1)
            new_id = old_id + "-%d" % time()

        if not (old_id and new_id):
            return True

        try:
            old_version = parent[old_id]
            api.content.transition(
                obj=old_version,
                transition="markForDeletion",
                comment="Auto archive item due to new version being published",
            )

            # Bypass user roles in order to rename old version
            oldSecurityManager = getSecurityManager()
            newSecurityManager(None, SpecialUsers.system)

            api.content.rename(obj=old_version, new_id=new_id)
            api.content.rename(obj=obj, new_id=old_id)
            obj.setEffectiveDate(DateTime())

            # Switch back to the current user
            setSecurityManager(oldSecurityManager)
        except Exception as err:
            logger.exception(err)
            return True
        return True


class RetractAndRenameOldVersionAddForm(NullAddForm):
    """Retract and rename old version addform"""

    def create(self):
        """Create content-rule"""
        return RetractAndRenameOldVersionAction()


class IEnableDisableDiscussionAction(Interface):
    """Enable/Disable Discussion settings schema"""

    action = schema.Choice(
        title="How discussions are changed",
        description="Should the discussions be disabled" "or enabled?",
        values=["enabled", "disabled"],
        required=True,
    )


@implementer(IEnableDisableDiscussionAction, IRuleElementData)
class EnableDisableDiscussionAction(SimpleItem):
    """Enable/Disable Discussion Action settings"""

    element = "eea.dexterity.indicators.enable_disable_discussion"
    action = None  # default value

    def summary(self):
        """Summary"""
        if self.action:
            return "Discussions will be %s" % self.action
        return "Not configured"


@implementer(IExecutable)
@adapter(Interface, IEnableDisableDiscussionAction, Interface)
class EnableDisableDiscussionActionExecutor(object):
    """Enable/Disable Discussion Action executor"""

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        # container = self.context
        # event = self.event
        action = self.element.action
        obj = self.event.object

        choice = {"enabled": 1, "disabled": 0}.get(action)

        if choice is None:
            return False

        if choice is not None:
            setattr(obj, "allow_discussion", bool(choice))

            logger.info(
                "Discussions for %s set to %s", obj.absolute_url(), action
            )
        else:
            logger.info(
                "eea.dexterity.indicators.actions.EnableDisable"
                "Discussion action is not properly configured"
            )
        return True


class EnableDisableDiscussionAddForm(AddForm):
    """Enable/Disable Discussion addform"""

    schema = IEnableDisableDiscussionAction
    label = "Add Enable/Disable Discussion Action"
    description = "A Enable/Disable Discussion action."
    form_name = "Configure element"


class EnableDisableDiscussionEditForm(EditForm):
    """Enable/Disable Discussion editform"""

    schema = IEnableDisableDiscussionAction
    label = "Edit Enable/Disable Discussion Action"
    description = "A Enable/Disable Discussion action."
    form_name = "Configure element"