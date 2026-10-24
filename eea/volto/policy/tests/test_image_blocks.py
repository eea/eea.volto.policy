"""Contracts for transient Image-title block enrichment."""

import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

from plone.app.contenttypes.interfaces import IImage
from zope.interface import alsoProvides


class ImageBlockTransformerTest(unittest.TestCase):
    def _image(self, title="Wetland bird", description="A bird stands in reeds."):
        image = SimpleNamespace(
            title=title, description=description, portal_type="Image"
        )
        alsoProvides(image, IImage)
        return image

    def _serialize(self, block, image=None, can_view=True):
        from eea.volto.policy.restapi.blocks import (
            ImageBlockSerializationTransformer,
        )

        transformer = ImageBlockSerializationTransformer(Mock(), Mock())
        with (
            patch(
                "eea.volto.policy.restapi.blocks.resolve_internal_image",
                return_value=image,
                create=True,
            ),
            patch(
                "eea.volto.policy.restapi.blocks.api.user.has_permission",
                return_value=can_view,
            ),
        ):
            return transformer(block)

    def test_serializer_runs_before_plone_resolveuid_transformer(self):
        from plone.restapi.serializer.blocks import ResolveUIDSerializer

        from eea.volto.policy.restapi.blocks import (
            ImageBlockSerializationTransformer,
            InternalURLPrefixSerializationTransformer,
        )

        self.assertEqual(ImageBlockSerializationTransformer.order, 0)
        self.assertEqual(ImageBlockSerializationTransformer.block_type, "image")
        self.assertEqual(ResolveUIDSerializer.order, 1)
        self.assertEqual(InternalURLPrefixSerializationTransformer.order, 10000)

    def test_empty_legacy_alt_follows_viewable_image_metadata_without_mutation(self):
        original = {
            "@type": "image",
            "url": "resolveuid/abc123",
            "alt": "",
        }
        stored = deepcopy(original)

        result = self._serialize(original, image=self._image())

        self.assertEqual(
            result,
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "",
                "alt_source": "image-metadata",
                "image_title": "Wetland bird",
                "image_description": "A bird stands in reeds.",
                "image_metadata": "Wetland bird: A bird stands in reeds.",
            },
        )
        self.assertEqual(original, stored)

    def test_legacy_alt_equal_to_metadata_normalizes_to_image_metadata_source(self):
        result = self._serialize(
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "Wetland bird: A bird stands in reeds.",
            },
            image=self._image(),
        )

        self.assertEqual(result["alt_source"], "image-metadata")
        self.assertEqual(result["alt"], "")
        self.assertEqual(result["image_title"], "Wetland bird")
        self.assertEqual(
            result["image_metadata"], "Wetland bird: A bird stands in reeds."
        )

    def test_legacy_alt_different_from_title_remains_custom(self):
        result = self._serialize(
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "Heron beside green reeds",
            },
            image=self._image(),
        )

        self.assertEqual(result["alt_source"], "custom")
        self.assertEqual(result["alt"], "Heron beside green reeds")
        self.assertEqual(result["image_title"], "Wetland bird")
        self.assertEqual(
            result["image_metadata"], "Wetland bird: A bird stands in reeds."
        )

    def test_case_or_punctuation_difference_remains_custom(self):
        for alt in ("wetland bird", "Wetland bird."):
            with self.subTest(alt=alt):
                result = self._serialize(
                    {
                        "@type": "image",
                        "url": "resolveuid/abc123",
                        "alt": alt,
                    },
                    image=self._image(),
                )

                self.assertEqual(result["alt_source"], "custom")
                self.assertEqual(result["alt"], alt)

    def test_missing_or_non_image_target_fails_safely(self):
        for target in (None, SimpleNamespace(title="Not an Image")):
            with self.subTest(target=target):
                result = self._serialize(
                    {
                        "@type": "image",
                        "url": "resolveuid/missing",
                        "alt": "",
                    },
                    image=target,
                )

                self.assertNotIn("image_title", result)

    def test_explicit_source_and_decorative_state_are_preserved(self):
        result = self._serialize(
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "Preserved custom value",
                "alt_source": "custom",
                "decorative": True,
            },
            image=self._image(),
        )

        self.assertEqual(result["alt_source"], "custom")
        self.assertEqual(result["alt"], "Preserved custom value")
        self.assertTrue(result["decorative"])
        self.assertEqual(result["image_title"], "Wetland bird")
        self.assertEqual(
            result["image_metadata"], "Wetland bird: A bird stands in reeds."
        )

    def test_private_image_title_is_not_exposed(self):
        result = self._serialize(
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "",
                "image_title": "Persisted stale title",
            },
            image=self._image("Restricted title"),
            can_view=False,
        )

        self.assertNotIn("image_title", result)
        self.assertNotIn("Restricted title", repr(result))
        self.assertNotIn("Persisted stale title", repr(result))

    def test_resolveuid_reference_resolves_an_image_without_network_access(self):
        from eea.volto.policy.restapi.blocks import resolve_internal_image

        image = self._image()
        with patch(
            "eea.volto.policy.restapi.blocks.api.content.get",
            return_value=image,
        ) as get:
            result = resolve_internal_image(Mock(), "resolveuid/abc-123")

        self.assertIs(result, image)
        get.assert_called_once_with(UID="abc-123")

    def test_portal_relative_legacy_reference_resolves_an_image(self):
        from eea.volto.policy.restapi.blocks import resolve_internal_image

        image = self._image()
        portal = Mock()
        portal.getId.return_value = "Plone"
        portal.restrictedTraverse.return_value = image
        with patch(
            "eea.volto.policy.restapi.blocks.api.portal.get",
            return_value=portal,
        ):
            result = resolve_internal_image(Mock(), "/Plone/en/wetland-bird")

        self.assertIs(result, image)
        portal.restrictedTraverse.assert_called_once_with("en/wetland-bird")

    def test_external_url_is_never_traversed(self):
        from eea.volto.policy.restapi.blocks import resolve_internal_image

        context = Mock()
        with patch("eea.volto.policy.restapi.blocks.api.content.get") as get:
            result = resolve_internal_image(
                context,
                "https://external.example/image.jpg",
            )

        self.assertIsNone(result)
        get.assert_not_called()
        context.restrictedTraverse.assert_not_called()

    def test_deserializer_strips_only_transient_image_metadata(self):
        from eea.volto.policy.restapi.blocks import (
            ImageBlockDeserializationTransformer,
        )

        transformer = ImageBlockDeserializationTransformer(Mock(), Mock())
        result = transformer(
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "Custom value",
                "alt_source": "custom",
                "decorative": True,
                "image_title": "Transient title",
                "image_description": "Transient desc",
                "image_metadata": "Transient metadata",
            }
        )

        self.assertEqual(
            result,
            {
                "@type": "image",
                "url": "resolveuid/abc123",
                "alt": "Custom value",
                "alt_source": "custom",
                "decorative": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
