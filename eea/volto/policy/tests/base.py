"""Base test layer for eea.volto.policy tests."""

from plone.app.testing import (
    TEST_USER_ID,
    IntegrationTesting,
    PloneSandboxLayer,
    applyProfile,
    setRoles,
)
from zope.configuration import xmlconfig

import eea.volto.policy


class EeaVoltoPolicyLayer(PloneSandboxLayer):
    """Layer that installs eea.volto.policy."""

    def setUpZope(self, app, configurationContext):
        xmlconfig.file("configure.zcml", eea.volto.policy, context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "eea.volto.policy:default")
        portal["portal_workflow"].setDefaultChain("simple_publication_workflow")
        setRoles(portal, TEST_USER_ID, ["Manager"])


EEA_VOLTO_POLICY_FIXTURE = EeaVoltoPolicyLayer()
EEA_VOLTO_POLICY_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EEA_VOLTO_POLICY_FIXTURE,),
    name="EeaVoltoPolicyLayer:Integration",
)
