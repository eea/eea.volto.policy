# pylint: disable = C0412
""" Base test cases
"""
from Products.CMFPlone import setuphandlers
from plone.testing import z2
from plone.app.testing import TEST_USER_ID
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import setRoles


try:
    # Plone 4
    from Products.CMFPlone.interfaces import IFactoryTool
    assert IFactoryTool
    IS_PLONE_4 = True
except ImportError:
    IS_PLONE_4 = False



class EEAFixture(PloneSandboxLayer):
    """ EEA Testing Policy
    """
    def setUpZope(self, app, configurationContext):
        """ Setup Zope
        """
        import eea.volto.policy
        self.loadZCML(package=eea.volto.policy)
        z2.installProduct(app, 'eea.volto.policy')

        # Plone 4
        if IS_PLONE_4:
            z2.installProduct(app, 'Products.DateRecurringIndex')


    def setUpPloneSite(self, portal):
        """ Setup Plone
        """
        applyProfile(portal, 'eea.volto.policy:default')

        # Default workflow
        wftool = portal['portal_workflow']
        wftool.setDefaultChain('simple_publication_workflow')

        # Login as manager
        setRoles(portal, TEST_USER_ID, ['Manager'])

        # Add default Plone content
        try:
            applyProfile(portal, 'plone.app.contenttypes:plone-content')
        except KeyError:
            # BBB Plone 4
            setuphandlers.setupPortalContent(portal)

        # Create testing environment
        portal.invokeFactory("Document", "sandbox", title="Sandbox")


    def tearDownZope(self, app):
        """ Uninstall Zope
        """
        z2.uninstallProduct(app, 'eea.volto.policy')

        # Plone 4
        if IS_PLONE_4:
            z2.uninstallProduct(app, 'Products.DateRecurringIndex')


EEAFIXTURE = EEAFixture()
FUNCTIONAL_TESTING = FunctionalTesting(bases=(EEAFIXTURE,),
                                       name='EEApolicy:Functional')
