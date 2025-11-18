"""Controlpanel utils"""

from zope.component import getUtilitiesFor
from zope.security.interfaces import IPermission
from zope.security import checkPermission
from Products.CMFCore.utils import getToolByName


def get_permission(name):
    """Get permission by name"""
    for _, permission in getUtilitiesFor(IPermission):
        if name in (permission.id, permission.title):
            return permission
    return None


def has_controlpanel_permission(context, request, panel):
    """Check if user has permission to access controlpanel"""
    if panel is None:
        request.response.setStatus(404)
        return None

    controlpanel_tool = getToolByName(context, "portal_controlpanel")
    panel_config = controlpanel_tool.getActionObject(
        "%s/%s" % (panel.configlet_category_id, panel.configlet_id)
    )

    permissionless = True

    for name in getattr(panel_config, "permissions", []):
        permission = get_permission(name)
        if not permission:
            continue
        has_permission = checkPermission(permission.id, context)
        if permission:
            permissionless = False
        if not permission or not has_permission:
            send_unauthorized(context, request)
            return False

    if not panel_config or permissionless:
        permission = get_permission("plone.app.controlpanel.Overview")
        has_permission = checkPermission(permission.id, context)
        if not permission or not has_permission:
            send_unauthorized(context, request)
            return False

    return True


def send_unauthorized(context, request):
    """Send unauthorized"""
    pm = getToolByName(context, "portal_membership")
    if bool(pm.isAnonymousUser()):
        request.response.setStatus(401)
    else:
        request.response.setStatus(403)
