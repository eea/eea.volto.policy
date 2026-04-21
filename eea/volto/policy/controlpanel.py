"""Header Controlpanel API"""

from zope.component import adapter
from zope.interface import Interface

from plone.restapi.controlpanels import RegistryConfigletPanel

from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer
from eea.volto.policy.interfaces import IHeaderProviderSchema


@adapter(Interface, IEeaVoltoPolicyLayer)
class HeaderControlpanel(RegistryConfigletPanel):
    """Header Control Panel"""

    schema = IHeaderProviderSchema
    schema_prefix = None
    configlet_id = "header-settings"
    configlet_category_id = "Products"
    title = "Header Settings"
    group = "Products"
    data = {"useAISearchIcon": True, "searchBox": []}
