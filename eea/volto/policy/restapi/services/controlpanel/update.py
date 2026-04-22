"""Controlpanel update service"""

from zExceptions import BadRequest
from plone.restapi.services.controlpanels.update import (
    ControlpanelsUpdate as PloneControlpanelsUpdate,
)
from eea.volto.policy.restapi.services.controlpanel.utils import (
    has_controlpanel_permission,
)


class ControlpanelsUpdate(PloneControlpanelsUpdate):
    """ " Controlpanel update service"""

    def reply(self):
        """Reply"""
        if not self.params:
            raise BadRequest("Missing parameter controlpanelname")
        panel = self.panel_by_name(self.params[0])

        if not has_controlpanel_permission(self.context, self.request, panel):
            return None

        return super().reply()
