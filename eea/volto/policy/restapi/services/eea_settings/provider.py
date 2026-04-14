"""Control panel provider for header search box settings."""

import json
import logging

from plone.api.portal import get_registry_record
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface

from eea.volto.policy.interfaces import IControlPanelProvider
from eea.volto.policy.interfaces import IHeaderProviderSchema

logger = logging.getLogger(__name__)


def process_registry_list(key, interface):
    """Process a registry list value."""
    value = get_registry_record(key, interface=interface)
    if isinstance(value, list):
        return value
    elif value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid JSON in {key} registry record")
    return []


@implementer(IControlPanelProvider)
@adapter(Interface, Interface)
class HeaderProvider:
    """Provides header configuration."""

    schema = IHeaderProviderSchema
    title = "Header"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        # Get registry record
        searchBox = process_registry_list("searchBox", IHeaderProviderSchema)
        useAISearchIcon = get_registry_record(
            "useAISearchIcon", interface=IHeaderProviderSchema
        )
        return {"header": {"searchBox": searchBox, "useAISearchIcon": useAISearchIcon}}
