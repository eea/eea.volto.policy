"""Siblings endpoint"""

from Acquisition import aq_base
from Acquisition import aq_inner
from plone import api
from plone.registry.interfaces import IRegistry
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.services import Service
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationTabs
from Products.CMFPlone.interfaces import INavigationSchema
from Products.Five import BrowserView
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implementer


def getNavigationRoot(context):
    """Get navigation root."""
    return "/".join(context.getPhysicalPath())


def get_url(item):
    """Get url."""
    if not item:
        return None

    if hasattr(aq_base(item), "getURL"):
        # Looks like a brain

        return item.getURL()

    return item.absolute_url()


def get_id(item):
    """Get id."""
    if not item:
        return None
    getId = getattr(item, "getId")

    if not utils.safe_callable(getId):
        # Looks like a brain
        return getId

    return getId()


def get_view_url(context):
    """Get view url."""
    registry = getUtility(IRegistry)
    view_action_types = registry.get("plone.types_use_view_action_in_listings", [])
    item_url = get_url(context)
    name = get_id(context)

    if getattr(context, "portal_type", {}) in view_action_types:
        item_url += "/view"
        name += "/view"

    return name, item_url


@implementer(INavigationTabs)
class CatalogNavigationTabs(BrowserView):
    """Catalog navigation tabs."""

    def _getNavQuery(self):
        """Check whether we only want actions."""
        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema, prefix="plone", check=False
        )
        customQuery = getattr(self.context, "getCustomNavQuery", False)

        if customQuery is not None and utils.safe_callable(customQuery):
            query = customQuery()
        else:
            query = {}

        query["path"] = {"query": getNavigationRoot(self.context), "depth": 1}
        query["portal_type"] = [t for t in navigation_settings.displayed_types]
        query["sort_on"] = navigation_settings.sort_tabs_on

        if navigation_settings.sort_tabs_reversed:
            query["sort_order"] = "reverse"
        else:
            query["sort_order"] = "ascending"

        if navigation_settings.filter_on_workflow:
            query["review_state"] = navigation_settings.workflow_states_to_show

        query["is_default_page"] = False

        if not navigation_settings.nonfolderish_tabs:
            query["is_folderish"] = True

        return query

    # pylint: disable=too-many-locals
    def topLevelTabs(self, actions=None, category="portal_tabs"):
        """Top level tabs."""
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
            result.append(data)

        # check whether we only want actions

        if not navigation_settings.generate_tabs:
            return result

        query = self._getNavQuery()

        rawresult = catalog.searchResults(query)

        def _get_url(item):
            """Get url for item.

            :param item:
            """
            if item.getRemoteUrl and not member == item.Creator:
                return (get_id(item), item.getRemoteUrl)

            return get_view_url(item)

        # now add the content to results

        # pylint: disable=unused-variable
        for item in rawresult:
            # if item.exclude_from_nav:
            #     continue
            cid, item_url = _get_url(item)
            data = {
                "name": utils.pretty_title_or_id(context, item),
                "id": item.getId,
                "url": item_url,
                "description": item.Description,
                "review_state": item.review_state,
            }
            result.append(data)

        return result


@implementer(IExpandableElement)
@adapter(Interface, Interface)
class Siblings:
    """Siblings."""

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False):
        result = {"siblings": {"@id": f"{self.context.absolute_url()}/@siblings"}}

        # unlike other expandable elements, expand is always True here

        if ("fullobjects" not in self.request.form) and not expand:
            return result

        portal = api.portal.get()

        if self.context is portal:
            return result

        tabObj = self.context.aq_parent.aq_inner
        items = tabObj.restrictedTraverse("localtabs_view").topLevelTabs(actions=())

        result["siblings"]["items"] = items

        return result


class SiblingsGet(Service):
    """Siblings - get."""

    def reply(self):
        """Reply."""
        siblings = Siblings(self.context, self.request)
        return siblings(expand=True)["siblings"]
