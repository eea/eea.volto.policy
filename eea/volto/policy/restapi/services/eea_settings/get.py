"""GET @eea.settings endpoint"""

from plone.restapi.services import Service
from zope.component import getAdapters

from eea.volto.policy.interfaces import IControlPanelProvider


class EEASettingsGet(Service):
    """GET @eea.settings endpoint - aggregates all providers."""

    def reply(self):
        result = {
            "@id": f"{self.context.absolute_url()}/@eea.settings",
        }
        for _, provider in getAdapters(
            (self.context, self.request), IControlPanelProvider
        ):
            result.update(provider())
        return result
