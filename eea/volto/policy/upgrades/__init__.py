""" Upgrades
"""
from plone import api


def upgrade_catalog(context):
    """upgrade portal catalog."""

    portal_setup = api.portal.get_tool("portal_setup")
    portal_setup.runImportStepFromProfile(
        "eea.volto.policy:volto_policy__23", "catalog")
