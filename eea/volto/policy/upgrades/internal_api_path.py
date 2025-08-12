"""Upgrade step to add registries"""


def add_internal_api_path_registry(context):
    """Upgrade step to import the control panel and registry configs."""
    profile_id = 'profile-eea.volto.policy:default'
    context.runImportStepFromProfile(profile_id, 'controlpanel')
    context.runImportStepFromProfile(profile_id, 'plone.app.registry')
