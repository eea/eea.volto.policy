"""Unified EEA Settings Controlpanel."""

from zope.component import adapter
from zope.component import getAdapters
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces import NotFound

from plone.restapi.controlpanels import RegistryConfigletPanel

from eea.volto.policy.interfaces import IControlPanelProvider
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer
from eea.volto.policy.interfaces import IEEASettingsControlpanel


@implementer(IEEASettingsControlpanel)
@adapter(Interface, IEeaVoltoPolicyLayer)
class EEASettingsControlpanel(RegistryConfigletPanel):
    """Unified control panel that aggregates all IControlPanelProvider
    adapters into a single panel with multiple fieldsets."""

    schema = None
    schema_prefix = None
    configlet_id = "eea-settings"
    configlet_category_id = "Products"
    title = "EEA Settings"
    group = "Products"

    def get_providers(self):
        """Discover all registered IControlPanelProvider adapters."""
        return getAdapters((self.context, self.request), IControlPanelProvider)

    def add(self, names):
        raise NotFound(self.context, names, self.request)

    def get(self, names):
        raise NotFound(self.context, names, self.request)

    def update(self, names):
        raise NotFound(self.context, names, self.request)

    def delete(self, names):
        raise NotFound(self.context, names, self.request)
