"""Control panel provider for header search box settings."""

import json
import logging

from plone.api.portal import get_registry_record
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface

from eea.volto.policy.interfaces import IControlPanelProvider
from eea.volto.policy.interfaces import IHeaderSearchBox, IBannerSchema

logger = logging.getLogger(__name__)


@implementer(IControlPanelProvider)
@adapter(Interface, Interface)
class HeaderSearchBoxProvider:
    """Provides headerconfiguration."""

    schema = IHeaderSearchBox
    schema_prefix = None
    title = "Header"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        raw = get_registry_record("headerSearchBox", interface=IHeaderSearchBox)
        if raw:
            try:
                return {"headerSearchBox": json.loads(raw)}
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid JSON in headerSearchBox registry record")
        return {"headerSearchBox": []}


@implementer(IControlPanelProvider)
@adapter(Interface, Interface)
class BannerProvider:
    """Provides banner configuration."""

    schema = IBannerSchema
    schema_prefix = None
    title = "Banner"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        title = get_registry_record("title", interface=IBannerSchema)
        description = get_registry_record(
            "description", interface=IBannerSchema
        )
        if title or description:
            return {
                "bannerSettings": {"title": title, "description": description}
            }
        return {"bannerSettings": {"title": "", "description": ""}}
