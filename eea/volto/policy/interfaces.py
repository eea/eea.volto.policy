# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from plone.volto.interfaces import IVoltoSettings
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope import schema
from zope.interface import Interface


class IEeaVoltoPolicyLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IInternalApiPathSettings(Interface):
    """Settings for URL replacement in update_internal_api_path script."""

    replacement_urls = schema.List(
        title="URLs to Replace",
        description="List of URLs that should be replaced with resolveuid references",
        value_type=schema.TextLine(),
        default=["http://localhost:8080", "http://backend:8080", "http://backend:6081"],
        required=False,
    )


class IInternalApiPathBatchSettings(Interface):
    """List of all processed urls"""

    last_processed_index = schema.Int(
        title="Last Processed Catalog Index",
        description="Stores last processed catalog index"
        "for URL replacement batch processing",
        default=0,
        required=False,
    )


class IInheritableFieldsSettings(Interface):
    """Settings for fields that support inheritance from ancestors."""

    fields = schema.List(
        title="Inheritable Fields",
        description="List of field names that can be inherited from "
        "ancestor objects when not set on the current object.",
        value_type=schema.TextLine(),
        default=["preview_image", "preview_caption"],
        required=False,
    )

    reindex_fields = schema.List(
        title="Inheritable fields to Reindex",
        description="List of field names that should trigger reindexing "
        "when inherited from ancestors.",
        value_type=schema.TextLine(),
        default=[],
        required=False,
    )


__all__ = [
    IVoltoSettings.__name__,
    "IInternalApiPathSettings",
    "IInternalApiPathBatchSettings",
    "IInheritableFieldsSettings",
]
