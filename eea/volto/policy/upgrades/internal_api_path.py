from plone import api

PROFILE_ID = "profile-eea.volto.policy:default"

def add_internal_api_path_registry(context):
    """Add IInternalApiPathSettings registry record."""
    setup = api.portal.get_tool("portal_setup")
    setup.runImportStepFromProfile(PROFILE_ID, "plone.app.registry")