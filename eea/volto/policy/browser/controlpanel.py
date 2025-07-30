# -*- coding: utf-8 -*-
"""Control panel for Internal API Path settings"""

from plone.app.registry.browser.controlpanel import (
    ControlPanelFormWrapper,
    RegistryEditForm,
)
from plone.z3cform import layout
from z3c.form import form, button
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
    label = u"Internal API Path Settings"
    description = u"Configure URLs that should be replaced with resolveuid references"

    @button.buttonAndHandler(u'Save', name='save')
    def handleSave(self, action):
        """Handle save button"""
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(
            u"Configuration updated.", "info"
        )

    @button.buttonAndHandler(u'Cancel', name='cancel')
    def handleCancel(self, action):
        """Handle cancel button"""
        IStatusMessage(self.request).addStatusMessage(
            u"Changes canceled.", "info"
        )
        self.request.response.redirect(
            f"{self.context.absolute_url()}/@@overview-controlpanel"
        )

    @button.buttonAndHandler(u'Update Internal API Paths', name='update_paths')
    def handleUpdatePaths(self, action):
        """Handle the update paths button"""
        # Redirect to the update view
        update_url = f"{self.context.absolute_url()}/@@update-internal-api-path"
        self.request.response.redirect(update_url)


class InternalApiPathControlPanelView(ControlPanelFormWrapper):
    """Control panel view wrapper"""
    form = InternalApiPathControlPanel
    label = u"Internal API Path Settings"
    description = u"Configure URLs that should be replaced with resolveuid references. Use the 'Update Internal API Paths' button to run the replacement process on all content."