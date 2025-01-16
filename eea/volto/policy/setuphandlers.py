""" Custom setup
"""
# pylint: disable = C0301
import logging

from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


logger = logging.getLogger("eea.volto.policy")


@implementer(INonInstallable)
class HiddenProfiles:
    """ Hidden profiles
    """

    def getNonInstallableProfiles(self):
        """ Hide uninstall profile from site-creation and quickinstaller.
        """
        return [
            'eea.volto.policy:multilingual',
            'eea.volto.policy:uninstall',
        ]


def post_install(context):
    """ Post install script
    """
    # Do something at the end of the installation of this package.


def uninstall(context):
    """ Uninstall script
    """
    # Do something at the end of the uninstallation of this package.
