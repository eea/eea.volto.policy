"""Breadcrumbs"""

# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.app.layout.navigation.root import getNavigationRoot
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationBreadcrumbs
from Products.CMFPlone.browser.navigation import get_view_url
from Products.CMFPlone.defaultpage import check_default_page_via_view
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.interface import implementer


@implementer(INavigationBreadcrumbs)
class PhysicalNavigationBreadcrumbs(BrowserView):
    """EEA Physical Navigation Breadcrumbs"""

    def breadcrumbs(self):
        """breadcrumbs"""
        context = aq_inner(self.context)
        request = self.request
        container = utils.parent(context)
        _name, item_url = get_view_url(context)
        # EEA add portal_type info to breadcrumbs
        last_crumb = {
            "absolute_url": item_url,
            "Title": utils.pretty_title_or_id(context, context),
            "portal_type": context.portal_type,
            "nav_title": getattr(aq_base(context), "nav_title", ""),
        }

        if container is None:
            return (last_crumb,)

        # Replicate Products.CMFPlone.browser.navigation.
        # RootPhysicalNavigationBreadcrumbs.breadcrumbs()
        # cause it is not registered during tests
        if INavigationRoot.providedBy(context):
            return ()

        view = getMultiAdapter((container, request), name="eea_breadcrumbs_view")
        base = tuple(view.breadcrumbs())

        # Some things want to be hidden from the breadcrumbs
        if IHideFromBreadcrumbs.providedBy(context):
            return base

        rootPath = getNavigationRoot(context)
        itemPath = "/".join(context.getPhysicalPath())

        # don't show default pages in breadcrumbs or pages above the navigation
        # root
        if not check_default_page_via_view(
            context, request
        ) and not rootPath.startswith(itemPath):
            base += (last_crumb,)
        return base
