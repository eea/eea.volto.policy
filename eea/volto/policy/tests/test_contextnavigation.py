"""Integration tests for the EEA context navigation endpoint."""

import unittest

from plone.app.testing import (
    TEST_USER_ID,
    TEST_USER_NAME,
    applyProfile,
    login,
    logout,
    setRoles,
)
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

        # Deep nesting to verify the plone.side_nav_depth bound:
        # level 1: published-child / draft-child, level 2: sub-draft,
        # level 3: deep-1, level 4: deep-2, level 5: deep-3
        sub = section["draft-child"]["sub-draft"]
        sub.invokeFactory("Document", "deep-1", title="Deep 1")
        sub["deep-1"].invokeFactory("Document", "deep-2", title="Deep 2")
        sub["deep-1"]["deep-2"].invokeFactory("Document", "deep-3", title="Deep 3")

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

    def test_bottom_level_zero_is_bounded_by_side_nav_depth(self):
        """bottomLevel=0 (no limit) must be bounded to plone.side_nav_depth.

        Default side_nav_depth is 4: items down to level 4 are shown,
        deeper ones (deep-3 at level 5) are cut off to avoid loading
        the whole site.
        """
        registry = getUtility(IRegistry)
        self.assertEqual(registry.get("plone.side_nav_depth"), 4)

        data = self._nav(self.portal.section, bottomLevel="0")
        titles = self._titles(data.get("items", []))

        self.assertIn("Published Child", titles)
        self.assertIn("Draft Child", titles)
        self.assertIn("Sub Draft", titles)
        self.assertIn("Deep 1", titles)
        self.assertIn("Deep 2", titles)
        self.assertNotIn("Deep 3", titles)

    def test_side_nav_depth_bound_is_configurable(self):
        """Raising plone.side_nav_depth shows more levels for bottomLevel=0."""
        registry = getUtility(IRegistry)
        registry["plone.side_nav_depth"] = 5

        data = self._nav(self.portal.section, bottomLevel="0")
        titles = self._titles(data.get("items", []))

        self.assertIn("Deep 2", titles)
        self.assertIn("Deep 3", titles)

    def test_explicit_bottom_level_is_not_bounded(self):
        """An explicit bottomLevel is honored as-is, not clamped."""
        data = self._nav(self.portal.section, bottomLevel="5")
        titles = self._titles(data.get("items", []))

        self.assertIn("Deep 2", titles)
        self.assertIn("Deep 3", titles)

    def test_to_13_upgrade_keeps_existing_registry_values(self):
        """The to_13 upgrade profile must not override registry values.

        It only creates the missing plone.side_nav_depth record via
        <records/>, which never writes values, so that TTW changes to
        other navigation settings survive the upgrade.
        """
        registry = getUtility(IRegistry)
        registry["plone.side_nav_depth"] = 6

        applyProfile(self.portal, "eea.volto.policy:to_13")

        self.assertEqual(registry.get("plone.side_nav_depth"), 6)


class TestContextNavigationPortalType(unittest.TestCase):
    """Test the portal_type fallback and inheritance from ancestor blocks.

    Resolution order: explicit request param > nearest ancestor
    contextNavigation (accordion) block > ``plone.side_nav_types``.
    """

    layer = EEA_VOLTO_POLICY_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.populateSite()

    def populateSite(self):
        """Create a section tree with private Document children."""
        self.portal.invokeFactory("Document", "subsite", title="Subsite")
        subsite = self.portal.subsite
        subsite.invokeFactory("Document", "child-a", title="Child A")
        subsite.invokeFactory("Document", "child-b", title="Child B")
        subsite["child-a"].invokeFactory("Document", "grandchild", title="Grandchild")

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

    def _set_ancestor_block(self, portal_type=None, variation="accordion"):
        """Attach a contextNavigation block to the subsite page."""
        block = {"@type": "contextNavigation", "variation": variation}
        if portal_type is not None:
            block["portal_type"] = portal_type
        self.portal.subsite.blocks = {"nav-block": block}

    def test_no_block_falls_back_to_registry_side_nav_types(self):
        """Without a block anywhere, the registry value is used as-is.

        With side_nav_types set to web_report* types, Document pages don't
        match and only the current page (injected via showAllParents) is
        listed. This pins the untouched registry fallback behavior: sections
        needing different types get an accordion block.
        """
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = (
            "web_report",
            "web_report_page",
            "web_report_section",
        )

        data = self._nav(self.portal.subsite["child-a"])
        titles = self._titles(data.get("items", []))

        self.assertIn("Child A", titles)
        self.assertNotIn("Child B", titles)

    def test_portal_type_inherited_from_ancestor_block(self):
        """A page without its own block inherits portal_type from the nearest
        ancestor holding a contextNavigation accordion block."""
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("web_report",)
        self._set_ancestor_block(portal_type=["Document"])

        data = self._nav(self.portal.subsite["child-a"])
        titles = self._titles(data.get("items", []))

        self.assertIn("Child B", titles)

    def test_nearest_ancestor_block_wins(self):
        """When nested ancestors both have blocks, the nearest one is used."""
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("Document",)
        self._set_ancestor_block(portal_type=["Document"])
        self.portal.subsite["child-a"].blocks = {
            "nav-block": {
                "@type": "contextNavigation",
                "variation": "accordion",
                "portal_type": ["Event"],
            }
        }

        data = self._nav(self.portal.subsite["child-a"]["grandchild"])
        titles = self._titles(data.get("items", []))

        # portal_type=Event (nearest ancestor) matches nothing: no Documents
        # are listed apart from the injected ancestors of the context page.
        self.assertNotIn("Child B", titles)

    def test_explicit_portal_type_wins_over_inherited(self):
        """An explicit portal_type request param beats the inherited one."""
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("web_report",)
        self._set_ancestor_block(portal_type=["Event"])

        data = self._nav(self.portal.subsite["child-a"], portal_type="Document")
        titles = self._titles(data.get("items", []))

        self.assertIn("Child B", titles)

    def test_block_without_portal_type_falls_back_to_registry(self):
        """An ancestor block without portal_type falls through to the
        plone.side_nav_types registry value."""
        self._set_ancestor_block()
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("web_report",)

        data = self._nav(self.portal.subsite["child-a"])
        titles = self._titles(data.get("items", []))

        self.assertNotIn("Child B", titles)

    def test_non_accordion_block_is_not_inherited(self):
        """Only the accordion variation is rendered as the side menu, so only
        it carries the config. A non-accordion nav block is ignored and the
        registry fallback applies."""
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("Document",)
        self._set_ancestor_block(portal_type=["Event"], variation="default")

        data = self._nav(self.portal.subsite["child-a"])
        titles = self._titles(data.get("items", []))

        # Documents show via the registry fallback (an inherited Event filter
        # would match nothing)
        self.assertIn("Child B", titles)

    def test_nested_nav_block_is_visited(self):
        """Accordion nav blocks nested in sections/columns (data.blocks) are
        found."""
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("web_report",)
        self.portal.subsite.blocks = {
            "columns-block": {
                "@type": "columns_block",
                "data": {
                    "blocks": {
                        "nav-in-column": {
                            "@type": "contextNavigation",
                            "variation": "accordion",
                            "portal_type": ["Document"],
                        }
                    },
                    "blocks_layout": {"items": ["nav-in-column"]},
                },
            }
        }

        data = self._nav(self.portal.subsite["child-a"])
        titles = self._titles(data.get("items", []))

        self.assertIn("Child B", titles)

    def test_inheritance_stops_without_view_permission_on_ancestor(self):
        """The aq_chain walk stops at the first non-viewable ancestor.

        Anonymous can see the published child page but not the private
        subsite, so the subsite block config must not be inherited and the
        plone.side_nav_types fallback applies instead.
        """
        registry = getUtility(IRegistry)
        registry["plone.side_nav_types"] = ("Document",)
        self._set_ancestor_block(portal_type=["Event"])
        workflow = self.portal.portal_workflow
        workflow.doActionFor(self.portal.subsite["child-a"], "publish")
        workflow.doActionFor(self.portal.subsite["child-b"], "publish")
        workflow.doActionFor(self.portal.subsite["child-a"]["grandchild"], "publish")

        logout()
        data = self._nav(self.portal.subsite["child-a"])
        titles = self._titles(data.get("items", []))

        # Documents show via the registry fallback, not the private
        # ancestor's Events.
        self.assertIn("Child A", titles)
        self.assertIn("Child B", titles)
        self.assertIn("Grandchild", titles)
