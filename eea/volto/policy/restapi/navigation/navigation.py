"""Navigation"""

from urllib.parse import urlparse

from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services.navigation.get import Navigation as BaseNavigation
from plone.restapi.serializer.utils import uid_to_url
from plone.restapi.services.navigation.get import (
    NavigationGet as BaseNavigationGet,
)
from Products.CMFCore.utils import getToolByName
from zope.component import adapter
from zope.interface import Interface, implementer
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer


@implementer(IExpandableElement)
@adapter(Interface, IEeaVoltoPolicyLayer)
class Navigation(BaseNavigation):
    """Navigation adapter"""

    def customize_entry(self, entry, brain):
        """append custom entries"""
        entry["brain"] = brain
        if hasattr(brain, "getRemoteUrl") and brain.getRemoteUrl:
            entry["path"] = urlparse(brain.getRemoteUrl).path
            pm = getToolByName(self.context, "portal_membership")
            if bool(pm.isAnonymousUser()):
                entry["@id"] = uid_to_url(brain.getRemoteUrl)

        return entry

    def render_item(self, item, path):
        """build navtree from item helper"""
        # prevents a crash in clms custom rendering
        # see also https://github.com/plone/plone.restapi/issues/1801
        if "path" not in item:
            return item

        sub = self.build_tree(item["path"], first_run=False)

        item.update({"items": sub})

        if "path" in item:
            del item["path"]

        if "brain" in item:
            del item["brain"]

        return item


class NavigationGet(BaseNavigationGet):
    """Navigation get service"""

    def reply(self):
        """reply"""
        navigation = Navigation(self.context, self.request)
        return navigation(expand=True)["navigation"]