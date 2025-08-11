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
        title=u"URLs to Replace",
        description=u"List of URLs that should be replaced with "
                    u"resolveuid references",
        value_type=schema.TextLine(),
        default=[
            u"http://localhost:8080",
            u"http://backend:8080",
            u"http://backend:6081"
        ],
        required=False,
    )

class IInternalApiPathBatchSettings(Interface):
    """List of all processed urls"""
    
    last_processed_index = schema.Int(
        title=u"Last Processed Catalog Index",
        description=u"Stores last processed catalog index for URL replacement batch processing",
        default=0,
        required=False,
    )

__all__ = [
    IVoltoSettings.__name__,
    "IInternalApiPathSettings",
    "IInternalApiPathBatchSettings",
]
