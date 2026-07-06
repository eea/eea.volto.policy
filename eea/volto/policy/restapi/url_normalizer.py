"""URL normalization helpers for Volto block serialization/deserialization."""

from __future__ import annotations

import os
from copy import deepcopy

INTERNAL_URL_PREFIXES_ENV = "INTERNAL_URL_PREFIXES"
URL_FIELDS = {"url", "href", "preview_image", "@id", "src"}


def get_internal_url_prefixes():
    """Return configured internal backend URL prefixes without trailing slash."""
    prefixes = []
    for value in os.environ.get(INTERNAL_URL_PREFIXES_ENV, "").split(","):
        value = value.strip().rstrip("/")
        if value:
            prefixes.append(value)
    return prefixes


def strip_internal_url_prefix(value):
    """Strip configured backend URL prefixes from a URL.

    Example, with INTERNAL_URL_PREFIXES=http://backend:8080/www::

        http://backend:8080/www/path?x=1#anchor -> /path?x=1#anchor

    Non-matching values are returned unchanged.
    """
    if not isinstance(value, str) or not value:
        return value

    for prefix in get_internal_url_prefixes():
        if value == prefix:
            return "/"
        if value.startswith(prefix + "/"):
            suffix = value[len(prefix):]
            return suffix or "/"
    return value


def normalize_url_fields(data, active_field=None):
    """Recursively strip configured internal URL prefixes in URL-like fields."""
    if isinstance(data, str):
        if active_field in URL_FIELDS:
            return strip_internal_url_prefix(data)
        return data

    if isinstance(data, list):
        return [normalize_url_fields(value, active_field=active_field) for value in data]

    if isinstance(data, dict):
        result = deepcopy(data)
        for field, value in result.items():
            result[field] = normalize_url_fields(value, active_field=field)
        return result

    return data


def normalize_html_attribute_url(value):
    """Strip configured internal URL prefixes from href/src attribute values."""
    return strip_internal_url_prefix(value)
