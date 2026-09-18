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


def test_suite():
    """Test suite."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
