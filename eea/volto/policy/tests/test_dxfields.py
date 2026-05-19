"""Tests for custom field serializers."""

import unittest

from plone.restapi.serializer import dxfields as restapi_dxfields

from eea.volto.policy.restapi.serializer import dxfields


class DummyField:
    """Small field double for serializer unit tests."""

    def __init__(self, name, value, interface_context=None):
        self.__name__ = name
        self.value = value
        self.interface_context = interface_context

    def get(self, context):
        return self.value

    def interface(self, context):
        return self.interface_context or context


class DummyContext:
    """Context double with field values as attributes."""


class EEAJSONFieldSerializerTest(unittest.TestCase):
    """Test EEA JSON field serialization additions."""

    def tearDown(self):
        dxfields.serialize_grouped_geolocation = self.original_serializer
        restapi_dxfields.json_compatible = self.original_json_compatible

    def setUp(self):
        self.original_serializer = dxfields.serialize_grouped_geolocation
        self.original_json_compatible = restapi_dxfields.json_compatible
        restapi_dxfields.json_compatible = lambda value: value

    def test_adds_grouped_geolocation_to_geo_coverage_from_behavior_value(self):
        context = DummyContext()
        metadata = DummyContext()
        metadata.geo_coverage = {
            "geolocation": [{"value": "geo-a", "label": "Austria"}]
        }
        field = DummyField(
            "geo_coverage",
            metadata.geo_coverage,
            interface_context=metadata,
        )

        def serializer(value, context=None):
            value = value.copy()
            value["grouped_geolocation"] = {"groups": [], "ungrouped": []}
            return value

        dxfields.serialize_grouped_geolocation = serializer

        self.assertEqual(
            dxfields.EEAJSONFieldSerializer(field, context, object())(),
            {
                "geolocation": [{"value": "geo-a", "label": "Austria"}],
                "grouped_geolocation": {"groups": [], "ungrouped": []},
            },
        )

    def test_leaves_other_json_fields_untouched(self):
        context = DummyContext()
        context.some_json = {"value": "unchanged"}
        field = DummyField("some_json", context.some_json)
        dxfields.serialize_grouped_geolocation = None

        self.assertEqual(
            dxfields.EEAJSONFieldSerializer(field, context, object())(),
            {"value": "unchanged"},
        )


def test_suite():
    """Test suite."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
