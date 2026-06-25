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


class DummyRequest:
    """Request double that supports attribute assignment for caching."""

    def __init__(self):
        pass


class GeoCoverageFieldSerializerTest(unittest.TestCase):
    """Test GeoCoverageFieldSerializer serialization additions."""

    def tearDown(self):
        dxfields.serialize_grouped_geolocation = self.original_serializer
        restapi_dxfields.json_compatible = self.original_json_compatible

    def setUp(self):
        self.original_serializer = dxfields.serialize_grouped_geolocation
        self.original_json_compatible = restapi_dxfields.json_compatible
        restapi_dxfields.json_compatible = lambda value: value

    def _make_geo_coverage_field(self, value, interface_context=None):
        """Create a DummyField marked with IGeoCoverageField."""
        from zope.interface import directlyProvides
        from eea.coremetadata.interfaces import IGeoCoverageField

        field = DummyField(
            "geo_coverage",
            value,
            interface_context=interface_context,
        )
        directlyProvides(field, IGeoCoverageField)
        return field

    def test_adds_grouped_geolocation_to_geo_coverage_from_behavior_value(self):
        context = DummyContext()
        metadata = DummyContext()
        metadata.geo_coverage = {
            "geolocation": [{"value": "geo-a", "label": "Austria"}]
        }
        field = self._make_geo_coverage_field(
            metadata.geo_coverage,
            interface_context=metadata,
        )

        def serializer(value, context=None):
            value = value.copy()
            value["grouped_geolocation"] = {"groups": [], "ungrouped": []}
            return value

        dxfields.serialize_grouped_geolocation = serializer

        self.assertEqual(
            dxfields.GeoCoverageFieldSerializer(field, context, DummyRequest())(),
            {
                "geolocation": [{"value": "geo-a", "label": "Austria"}],
                "grouped_geolocation": {"groups": [], "ungrouped": []},
            },
        )

    def test_adds_grouped_geolocation_from_context_attribute(self):
        context = DummyContext()
        context.geo_coverage = {
            "geolocation": [{"value": "geo-b", "label": "Belgium"}]
        }
        field = self._make_geo_coverage_field(
            context.geo_coverage,
            interface_context=context,
        )

        def serializer(value, context=None):
            value = value.copy()
            value["grouped_geolocation"] = {"groups": [], "ungrouped": []}
            return value

        dxfields.serialize_grouped_geolocation = serializer

        self.assertEqual(
            dxfields.GeoCoverageFieldSerializer(field, context, DummyRequest())(),
            {
                "geolocation": [{"value": "geo-b", "label": "Belgium"}],
                "grouped_geolocation": {"groups": [], "ungrouped": []},
            },
        )

    def test_handles_non_dict_value_gracefully(self):
        context = DummyContext()
        field = self._make_geo_coverage_field(None)

        # When value is None, serializer returns None and we don't call
        # serialize_grouped_geolocation (isinstance check fails)
        result = dxfields.GeoCoverageFieldSerializer(
            field, context, DummyRequest()
        )()
        # DefaultFieldSerializer returns None for missing values
        self.assertIsNone(result)


def test_suite():
    """Test suite."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
