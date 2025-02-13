from Acquisition import aq_inner
from Missing import Missing
from plone.app.layout.navigation.root import getNavigationRoot
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationTabs
from Products.CMFPlone.browser.navigation import get_id
from Products.CMFPlone.browser.navigation import get_view_url
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import implementer
from plone.volto.browser.navigation import CatalogNavigationTabs as BaseCatalogNavigationTabs

from plone.restapi.serializer.utils import uid_to_url

try:
    from plone.base.interfaces import INavigationSchema
except ImportError:
    from Products.CMFPlone.interfaces import INavigationSchema

@implementer(INavigationTabs)
class CatalogNavigationTabs(BaseCatalogNavigationTabs):
    """ Catalog Navigation Tabs customization to fix remote url issue
    """
    def topLevelTabs(self, actions=None, category="portal_tabs"):
        context = aq_inner(self.context)
        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema, prefix="plone", check=False
        )
        mtool = getToolByName(context, "portal_membership")
        member = mtool.getAuthenticatedMember().id
        catalog = getToolByName(context, "portal_catalog")

        if actions is None:
            context_state = getMultiAdapter(
                (context, self.request), name="plone_context_state"
            )
            actions = context_state.actions(category)

        # Build result dict
        result = []
        # first the actions
        for actionInfo in actions:
            data = actionInfo.copy()
            data["name"] = data["title"]
            self.customize_entry(data)
            result.append(data)

        # check whether we only want actions
        if not navigation_settings.generate_tabs:
            return result

        query = self._getNavQuery()
        print('query', query)
        rawresult = catalog.searchResults(query)


        def _get_url(item):
            if item.getRemoteUrl and not member == item.Creator:
                # fix remote url issue by calling uid_to_url on remote url
                return (get_id(item), uid_to_url(item.getRemoteUrl))
            return get_view_url(item)

        context_path = "/".join(context.getPhysicalPath())

        # now add the content to results
        for item in rawresult:
            if item.exclude_from_nav and not context_path.startswith(
                item.getPath()
            ):  # noqa: E501
                # skip excluded items if they're not in our context path
                continue
            cid, item_url = _get_url(item)
            print('item_url', item_url)

            # Guard in case the nav_title field behavior is not applied to the
            # object and returns 'Missing.Value'
            if getattr(item, "nav_title", "").__class__ == Missing:
                nav_title = ""
            else:
                nav_title = getattr(item, "nav_title", "")

            data = {
                "name": nav_title or utils.pretty_title_or_id(context, item),
                "id": item.getId,
                "url": item_url,
                "description": item.Description,
                "review_state": item.review_state,
            }
            self.customize_entry(data, item)
            result.append(data)

        return result