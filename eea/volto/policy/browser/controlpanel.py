# -*- coding: utf-8 -*-
"""Control panel for Internal API Path settings"""

from plone.app.registry.browser.controlpanel import (
    ControlPanelFormWrapper,
    RegistryEditForm,
)
from z3c.form import button
from zope.interface import implementer
from zope.interface import Interface
from Products.statusmessages.interfaces import IStatusMessage

from eea.volto.policy.interfaces import IInternalApiPathSettings


class IInternalApiPathControlPanel(Interface):
    """Marker interface for the control panel"""


@implementer(IInternalApiPathControlPanel)
class InternalApiPathControlPanel(RegistryEditForm):
    """Control panel form for Internal API Path settings"""

    schema = IInternalApiPathSettings
    schema_prefix = "eea.volto.policy.internal_api_path"
    label = "Internal API Path Correction"
    description = (
        "Configure and fix internal API paths by replacing "
        "backend URLs with resolveuid references"
    )

    @button.buttonAndHandler("Save", name="save")
    def handleSave(self, action):
        """Handle save button"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage("Configuration updated.", "info")

    @button.buttonAndHandler("Cancel", name="cancel")
    def handleCancel(self, action):
        """Handle cancel button"""
        IStatusMessage(self.request).addStatusMessage("Changes canceled.", "info")
        self.request.response.redirect(
            self.context.absolute_url() + "/@@overview-controlpanel"
        )

    @button.buttonAndHandler("Fix Internal API Paths", name="update_paths")
    def handleUpdatePaths(self, action):
        """Handle the fix paths button"""
        # Redirect to the update view
        update_url = self.context.absolute_url() + "/@@update-internal-api-path"
        self.request.response.redirect(update_url)


class InternalApiPathControlPanelView(ControlPanelFormWrapper):
    """Control panel view wrapper"""

    form = InternalApiPathControlPanel
    label = "Internal API Path Correction"
    description = (
        "Configure and fix internal API paths by replacing backend URLs with "
        "resolveuid references. Use the 'Fix Internal API Paths' button to "
        "run the correction process on all content."
    )
