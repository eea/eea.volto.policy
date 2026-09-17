"""Tests for the EEA Subsite behavior."""

import unittest

from plone.autoform.interfaces import IFormFieldProvider

from eea.volto.policy.behaviors.subsite import ISubsiteLogoMain


class SubsiteLogoMainBehaviorTest(unittest.TestCase):
    """Verify the behavior schema exposed to Dexterity."""

    def test_schema_is_a_form_field_provider(self):
        self.assertTrue(IFormFieldProvider.providedBy(ISubsiteLogoMain))

    def test_field_defaults_to_false(self):
        field = ISubsiteLogoMain["subsite_logo_main"]

        self.assertFalse(field.default)
        self.assertFalse(field.required)
        self.assertEqual(field.title, "Use as main logo")

    def test_subsite_restapi_customization_is_available(self):
        try:
            from collective.volto.subsites.restapi.services.subsite.get import (
                Subsite as BaseSubsite,
            )
            from collective.volto.subsites.restapi.services.subsite.get import (
                SubsiteGet as BaseSubsiteGet,
            )
            from eea.volto.policy.restapi.services.subsite.get import Subsite
            from eea.volto.policy.restapi.services.subsite.get import SubsiteGet
        except ImportError:
            self.skipTest("collective.volto.subsites is not installed")

        self.assertTrue(issubclass(Subsite, BaseSubsite))
        self.assertTrue(issubclass(SubsiteGet, BaseSubsiteGet))


def test_suite():
    """Test suite."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
