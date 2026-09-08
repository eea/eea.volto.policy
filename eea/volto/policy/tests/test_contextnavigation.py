"""Integration tests for the EEA context navigation endpoint."""

import unittest

from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, logout, setRoles
from plone.base.interfaces import INavigationSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

from eea.volto.policy.restapi.services.contextnavigation.get import EEAContextNavigation
from eea.volto.policy.tests.base import EEA_VOLTO_POLICY_INTEGRATION_TESTING


class TestContextNavigationWorkflow(unittest.TestCase):
    """Test that contextnavigation respects view permissions, not workflow."""

    layer = EEA_VOLTO_POLICY_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.populateSite()

    def populateSite(self):
        """Create a small page tree with published and draft children."""
        self.portal.invokeFactory("Document", "section", title="Section")
        section = self.portal.section

        section.invokeFactory("Document", "published-child", title="Published Child")
        section.invokeFactory("Document", "draft-child", title="Draft Child")

        # Publish the section and one child; leave the other private.
        self.portal.portal_workflow.doActionFor(section, "publish")
        self.portal.portal_workflow.doActionFor(section["published-child"], "publish")

        # Add a nested draft page to verify bottomLevel=0 expands fully.
        section["draft-child"].invokeFactory("Document", "sub-draft", title="Sub Draft")

        # Force the site-wide workflow filter to "published only".  The fix
        # must remove this hard-coded restriction from the lateral nav query
        # so that users with view permission still see draft/private items.
        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema, prefix="plone", check=False
        )
        navigation_settings.filter_on_workflow = True
        navigation_settings.workflow_states_to_show = ("published",)

    def _titles(self, items):
        """Flatten item titles recursively."""
        result = []
        for item in items:
            result.append(item["title"])
            result.extend(self._titles(item.get("items", [])))
        return result

    def _nav(self, context, **params):
        """Call the context navigation endpoint adapter directly."""
        self.request.form.clear()
        for key, value in params.items():
            self.request.form[f"expand.contextnavigation.{key}"] = value
        return EEAContextNavigation(context, self.request)(expand=True)[
            "contextnavigation"
        ]

    def test_manager_sees_draft_siblings_despite_workflow_filter(self):
        """A user with view permission sees draft siblings in the nav."""
        data = self._nav(self.portal.section)
        titles = self._titles(data.get("items", []))

        self.assertIn("Published Child", titles)
        self.assertIn("Draft Child", titles)
        self.assertIn("Sub Draft", titles)

    def test_anonymous_does_not_see_draft_items(self):
        """Anonymous users still only see published items."""
        logout()
        data = self._nav(self.portal.section)
        titles = self._titles(data.get("items", []))

        self.assertIn("Published Child", titles)
        self.assertNotIn("Draft Child", titles)
        self.assertNotIn("Sub Draft", titles)

    def test_bottom_level_zero_returns_all_descendants(self):
        """bottomLevel=0 must return the whole tree, not just current page."""
        data = self._nav(self.portal.section, bottomLevel="0")
        titles = self._titles(data.get("items", []))

        self.assertIn("Published Child", titles)
        self.assertIn("Draft Child", titles)
        self.assertIn("Sub Draft", titles)
