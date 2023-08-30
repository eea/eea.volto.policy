# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""
from plone.volto.interfaces import IVoltoSettings
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IEeaVoltoPolicyLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""

__all__ = [
    IVoltoSettings.__name__,
]
