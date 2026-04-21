"""GET @header-settings endpoint"""

import json
import logging

from plone.api.portal import get_registry_record
from plone.restapi.services import Service

from eea.volto.policy.interfaces import IHeaderProviderSchema

logger = logging.getLogger(__name__)


def _process_registry_list(key):
    """Coerce registry value into a list."""
    value = get_registry_record(key, interface=IHeaderProviderSchema)
    if isinstance(value, list):
        return value
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid JSON in %s registry record", key)
    return []


class HeaderSettingsGet(Service):
    """Public GET @header-settings endpoint."""

    def reply(self):
        return {
            "@id": f"{self.context.absolute_url()}/@header-settings",
            "useAISearchIcon": get_registry_record(
                "useAISearchIcon", interface=IHeaderProviderSchema
            ),
            "searchBox": _process_registry_list("searchBox"),
        }
