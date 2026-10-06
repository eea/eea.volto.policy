"""Integration tests for the EEA siblings endpoint."""

import unittest

from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, logout, setRoles
from plone.base.interfaces import INavigationSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from eea.volto.policy.restapi.services.siblings.get import Siblings
from eea.volto.policy.tests.base import EEA_VOLTO_POLICY_INTEGRATION_TESTING


class TestSiblingsWorkflow(unittest.TestCase):
    """Test that siblings respects view permissions, not workflow."""

    layer = EEA_VOLTO_POLICY_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.populateSite()

    def populateSite(self):
        """Create a folder with published and draft children."""
        self.portal.invokeFactory("Document", "section", title="Section")
        section = self.portal.section

        section.invokeFactory("Document", "published-child", title="Published Child")
        section.invokeFactory("Document", "draft-child", title="Draft Child")

        # Publish the section and one child; leave the other private.
        self.portal.portal_workflow.doActionFor(section, "publish")
        self.portal.portal_workflow.doActionFor(section["published-child"], "publish")

        # Force the site-wide workflow filter to "published only". The fix
        # must remove this hard-coded restriction from the siblings query
        # so that users with view permission still see draft/private items.
        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema, prefix="plone", check=False
        )
        navigation_settings.filter_on_workflow = True
        navigation_settings.workflow_states_to_show = ("published",)

    def _siblings(self, context):
        """Call the siblings expandable element directly."""
        return Siblings(context, self.request)(expand=True)["siblings"]["items"]

    def _names(self, items):
        return [item["name"] for item in items]

    def test_manager_sees_draft_siblings_despite_workflow_filter(self):
        """A user with view permission sees draft siblings."""
        items = self._siblings(self.portal.section["published-child"])
        names = self._names(items)

        self.assertIn("Published Child", names)
        self.assertIn("Draft Child", names)

    def test_anonymous_does_not_see_draft_siblings(self):
        """Anonymous users still only see published siblings."""
        logout()
        items = self._siblings(self.portal.section["published-child"])
        names = self._names(items)

        self.assertIn("Published Child", names)
        self.assertNotIn("Draft Child", names)
