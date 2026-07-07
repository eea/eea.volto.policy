"""Unit tests for URL normalization helpers."""

import os
import unittest
from unittest.mock import patch

from eea.volto.policy.restapi.url_normalizer import (
    INTERNAL_URL_PREFIXES_ENV,
    get_internal_url_prefixes,
    normalize_html_attribute_url,
    normalize_url_fields,
    strip_internal_url_prefix,
)

PREFIX = "http://backend:8080/www"
PREFIX2 = "https://internal.localhost/Plone"


class GetInternalUrlPrefixesTest(unittest.TestCase):
    """Tests for get_internal_url_prefixes()."""

    def test_returns_empty_list_when_env_unset(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_internal_url_prefixes(), [])

    def test_returns_empty_list_when_env_empty_string(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: ""}):
            self.assertEqual(get_internal_url_prefixes(), [])

    def test_returns_single_prefix_without_trailing_slash(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(get_internal_url_prefixes(), [PREFIX])

    def test_strips_trailing_slash_from_prefix(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX + "/"}):
            self.assertEqual(get_internal_url_prefixes(), [PREFIX])

    def test_strips_whitespace_around_prefix(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: "  " + PREFIX + "  "}):
            self.assertEqual(get_internal_url_prefixes(), [PREFIX])

    def test_returns_multiple_prefixes(self):
        env_val = f"  {PREFIX} , {PREFIX2}/  ,  "
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: env_val}):
            self.assertEqual(get_internal_url_prefixes(), [PREFIX, PREFIX2])

    def test_skips_empty_entries_in_comma_list(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: f",{PREFIX},,"}):
            self.assertEqual(get_internal_url_prefixes(), [PREFIX])


class StripInternalUrlPrefixTest(unittest.TestCase):
    """Tests for strip_internal_url_prefix()."""

    def test_returns_non_string_unchanged(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertIsNone(strip_internal_url_prefix(None))
            self.assertEqual(strip_internal_url_prefix(42), 42)
            self.assertEqual(strip_internal_url_prefix(["a"]), ["a"])

    def test_returns_empty_string_unchanged(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(strip_internal_url_prefix(""), "")

    def test_returns_value_unchanged_when_no_prefixes_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            url = f"{PREFIX}/some/path"
            self.assertEqual(strip_internal_url_prefix(url), url)

    def test_strips_matching_prefix(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(
                strip_internal_url_prefix(f"{PREFIX}/some/path"),
                "/some/path",
            )

    def test_preserves_query_and_fragment(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(
                strip_internal_url_prefix(f"{PREFIX}/path?x=1#anchor"),
                "/path?x=1#anchor",
            )

    def test_returns_root_when_value_equals_prefix(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(strip_internal_url_prefix(PREFIX), "/")

    def test_does_not_strip_partial_match(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            # "http://backend:8080/wwwextra" must NOT match PREFIX
            self.assertEqual(
                strip_internal_url_prefix(f"{PREFIX}extra"),
                f"{PREFIX}extra",
            )

    def test_does_not_strip_non_matching_prefix(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(
                strip_internal_url_prefix("http://other.example.com/path"),
                "http://other.example.com/path",
            )

    def test_strips_with_multiple_prefixes(self):
        env_val = f"{PREFIX},{PREFIX2}"
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: env_val}):
            self.assertEqual(
                strip_internal_url_prefix(f"{PREFIX}/a"),
                "/a",
            )
            self.assertEqual(
                strip_internal_url_prefix(f"{PREFIX2}/b"),
                "/b",
            )

    def test_strips_trailing_slash_prefix_from_env(self):
        # Prefix stored with trailing slash should still match
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX + "/"}):
            self.assertEqual(
                strip_internal_url_prefix(f"{PREFIX}/some/page"),
                "/some/page",
            )


class NormalizeUrlFieldsTest(unittest.TestCase):
    """Tests for normalize_url_fields()."""

    def test_returns_non_dict_non_list_non_str_unchanged(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(normalize_url_fields(42), 42)
            self.assertIsNone(normalize_url_fields(None))
            self.assertTrue(normalize_url_fields(True))

    def test_strips_url_field_in_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"url": f"{PREFIX}/path/to/page"}
            self.assertEqual(
                normalize_url_fields(data),
                {"url": "/path/to/page"},
            )

    def test_strips_href_field_in_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"href": f"{PREFIX}/link"}
            self.assertEqual(normalize_url_fields(data), {"href": "/link"})

    def test_strips_src_field_in_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"src": f"{PREFIX}/image.png"}
            self.assertEqual(normalize_url_fields(data), {"src": "/image.png"})

    def test_strips_at_id_field_in_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"@id": f"{PREFIX}/content"}
            self.assertEqual(normalize_url_fields(data), {"@id": "/content"})

    def test_strips_preview_image_field_in_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"preview_image": f"{PREFIX}/preview.jpg"}
            self.assertEqual(
                normalize_url_fields(data),
                {"preview_image": "/preview.jpg"},
            )

    def test_does_not_strip_non_url_field(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"title": f"{PREFIX}/should/not/be/stripped"}
            result = normalize_url_fields(data)
            self.assertEqual(
                result["title"],
                f"{PREFIX}/should/not/be/stripped",
            )

    def test_strips_url_fields_in_nested_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {
                "blocks": {
                    "abc-123": {
                        "@type": "image",
                        "url": f"{PREFIX}/media/photo.jpg",
                    },
                },
            }
            result = normalize_url_fields(data)
            self.assertEqual(
                result["blocks"]["abc-123"]["url"],
                "/media/photo.jpg",
            )

    def test_strips_url_fields_in_list_of_dicts(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {
                "items": [
                    {"url": f"{PREFIX}/a"},
                    {"url": f"{PREFIX}/b"},
                ],
            }
            result = normalize_url_fields(data)
            self.assertEqual(result["items"][0]["url"], "/a")
            self.assertEqual(result["items"][1]["url"], "/b")

    def test_strips_url_field_inside_list(self):
        # When a list is the value of a url field, each string is stripped
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"url": [f"{PREFIX}/one", f"{PREFIX}/two"]}
            result = normalize_url_fields(data)
            self.assertEqual(result["url"], ["/one", "/two"])

    def test_does_not_strip_strings_in_non_url_list(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"tags": [f"{PREFIX}/tag1", f"{PREFIX}/tag2"]}
            result = normalize_url_fields(data)
            self.assertEqual(result["tags"], [f"{PREFIX}/tag1", f"{PREFIX}/tag2"])

    def test_noop_when_no_prefixes_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            data = {"url": f"{PREFIX}/path", "title": "hello"}
            self.assertEqual(normalize_url_fields(data), data)

    def test_does_not_mutate_original_data(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {"url": f"{PREFIX}/path"}
            normalize_url_fields(data)
            self.assertEqual(data["url"], f"{PREFIX}/path")

    def test_handles_empty_dict(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(normalize_url_fields({}), {})

    def test_handles_empty_list(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(normalize_url_fields([]), [])

    def test_preserves_non_url_fields_alongside_url_fields(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {
                "@type": "image",
                "url": f"{PREFIX}/photo.jpg",
                "title": "My Photo",
                "alt": f"{PREFIX}/not-stripped",
            }
            result = normalize_url_fields(data)
            self.assertEqual(result["@type"], "image")
            self.assertEqual(result["url"], "/photo.jpg")
            self.assertEqual(result["title"], "My Photo")
            self.assertEqual(result["alt"], f"{PREFIX}/not-stripped")

    def test_deeply_nested_structure(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            data = {
                "blocks": {
                    "block-1": {
                        "@type": "slate",
                        "value": [
                            {"children": [{"url": f"{PREFIX}/deep"}]},
                        ],
                    },
                    "block-2": {
                        "@type": "html",
                        "html": "<p>unchanged</p>",
                    },
                },
            }
            result = normalize_url_fields(data)
            self.assertEqual(
                result["blocks"]["block-1"]["value"][0]["children"][0]["url"],
                "/deep",
            )
            self.assertEqual(
                result["blocks"]["block-2"]["html"],
                "<p>unchanged</p>",
            )


class NormalizeHtmlAttributeUrlTest(unittest.TestCase):
    """Tests for normalize_html_attribute_url()."""

    def test_strips_prefix_from_href_value(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(
                normalize_html_attribute_url(f"{PREFIX}/page"),
                "/page",
            )

    def test_returns_non_matching_unchanged(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertEqual(
                normalize_html_attribute_url("https://example.com/page"),
                "https://example.com/page",
            )

    def test_returns_value_unchanged_when_no_prefixes(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                normalize_html_attribute_url(f"{PREFIX}/page"),
                f"{PREFIX}/page",
            )

    def test_returns_non_string_unchanged(self):
        with patch.dict(os.environ, {INTERNAL_URL_PREFIXES_ENV: PREFIX}):
            self.assertIsNone(normalize_html_attribute_url(None))


class DownloadImageUrlRegressionTest(unittest.TestCase):
    """Regression test for the space-in-URL bug.

    The image download URL must NOT contain a space between the resolved
    path and /@@download/image.
    """

    def test_no_space_in_download_image_url(self):
        from eea.volto.policy.restapi.blocks import HTMLBlockSerializerBase

        # Extract the _resolve_uid logic by checking the source does not
        # contain the buggy pattern with a space.
        import inspect

        source = inspect.getsource(HTMLBlockSerializerBase._resolve_uid)
        self.assertNotIn(
            "} /@@download/image",
            source,
            "Found space before /@@download/image — regression of the "
            "f-string spacing bug.",
        )
        self.assertIn(
            "}/@@download/image",
            source,
            "Expected no space before /@@download/image in the f-string.",
        )


def test_suite():
    """Test suite."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
