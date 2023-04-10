# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""
from eea.volto.policy import EEAMessageFactory as _
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IEeaVoltoPolicyLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IVoltoSettings(Interface):
    """Volto settings necessary to store in the backend"""

    frontend_domain = schema.URI(
        title="Frontend domain",
        description=_("Used for rewriting URL's sent in the password reset "
                      "e-mail by Plone."),
        default="http://localhost:3000",
    )
