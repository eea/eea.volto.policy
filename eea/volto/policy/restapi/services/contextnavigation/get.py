"""EEA Context Navigation"""

from zope.component import getUtility
from zope.component import adapter
from zope.schema.interfaces import IFromUnicode
from zope.interface import implementer
from zope.interface import Interface
from Products.CMFPlone.utils import normalizeString
from plone.app.layout.navigation.root import getNavigationRoot
from plone.app.dexterity import _
from plone.restapi.services.contextnavigation import get as original_get
from plone.restapi.interfaces import IExpandableElement, IPloneRestapiLayer
from plone.registry.interfaces import IRegistry
from plone.restapi import bbb as restapi_bbb
from plone.restapi.bbb import safe_hasattr
from plone import schema
from plone import api


class IEEANavigationPortlet(original_get.INavigationPortlet):
    """Custom schema for navigation portlet"""

    portal_type = schema.Tuple(
        title=_("Displayed content types"),
        description=_("The content types that should be shown in the navigati"
                      "on"),
        required=False,
        default=(),
        missing_value=(),
        value_type=schema.Choice(
            source="plone.app.vocabularies.ReallyUserFriendlyTypes"
        ),
    )


class IEEAContextNavigationSchema(restapi_bbb.INavigationSchema):
    """Custom schema for context navigation"""

    side_nav_types = schema.Tuple(
        title=_("Displayed content types within the side navigation"),
        description=_("The content types that should be shown in the "
                      "side navigation"),
        required=False,
        default=("Document",),
        missing_value=(),
        value_type=schema.Choice(
            source="plone.app.vocabularies.ReallyUserFriendlyTypes"
        ),
    )


restapi_bbb.INavigationSchema = IEEAContextNavigationSchema

def eea_extract_data(_obj_schema, raw_data, prefix):
    """Custom extract data function for navigation portlet"""
    obj_schema = IEEANavigationPortlet
    obj_schema_names = list(obj_schema)
    data = original_get.Data({})
    for name in obj_schema_names:
        field = obj_schema[name]
        raw_value = raw_data.get(prefix + name, field.default)

        if isinstance(field, schema.Tuple):
            value = raw_value.split(',') if ',' in raw_value else raw_value
        else:
            value = IFromUnicode(field).fromUnicode(raw_value)

        data[name] = value

    return data


class EEAContextNavigationQueryBuilder(original_get.QueryBuilder):
    """Custom QueryBuilder for context navigation"""

    def getSideNavTypes(self, context):
        """Get the side navigation types"""
        registry = getUtility(IRegistry)
        return registry.get("plone.side_nav_types", ())

    def __init__(self, context, data):
        super().__init__(context, data)

        depth = data.bottomLevel

        if depth == 0:
            depth = 999

        root = original_get.get_root(context, data.root_path)
        if root is not None:
            rootPath = "/".join(root.getPhysicalPath())
        else:
            rootPath = getNavigationRoot(context)

        # EEA modification to always use the rootPath for query
        self.query["path"] = {"query": rootPath, "depth": depth,
                              "navtree": 1}

        self.query["portal_type"] = data.portal_type or self.getSideNavTypes(
            context)

        topLevel = data.topLevel
        if topLevel and topLevel > 0:
            # EEA modification to use bottomLevel for depth of navtree_start
            self.query["path"]["navtree_start"] = depth


original_get.QueryBuilder = EEAContextNavigationQueryBuilder


class EEANavigationPortletRenderer(original_get.NavigationPortletRenderer):
    """Custom NavigationPortletRenderer for context navigation"""

    def render(self):
        """Render the navigation portlet"""
        res = {
            "title": self.title(),
            "url": self.heading_link_target(),
            "has_custom_name": bool(self.hasName()),
            "items": [],
            "available": self.available,
        }
        if not res["available"]:
            return res

        if self.include_top():
            root = self.navigation_root()
            root_is_portal = self.root_is_portal()

            if root is None:
                root = self.urltool.getPortalObject()
                root_is_portal = True

            if safe_hasattr(self.context, "getRemoteUrl"):
                root_url = root.getRemoteUrl()
            else:
                # cid, root_url = get_view_url(root)
                # cid = get_id(root)
                root_url = original_get.get_url(root)

            root_title = "Home" if root_is_portal else \
                root.pretty_title_or_id()
            root_type = (
                "plone-site"
                if root_is_portal
                else normalizeString(root.portal_type, context=root)
            )
            normalized_id = normalizeString(root.Title(), context=root)

            if root_is_portal:
                state = ""
            else:
                state = api.content.get_state(root)

            res["items"].append(
                {
                    "@id": root.absolute_url(),
                    "description": root.Description() or "",
                    "href": root_url,
                    "icon": "",
                    "is_current": bool(self.root_item_class()),
                    "is_folderish": True,
                    "is_in_path": True,
                    "items": [],
                    "normalized_id": normalized_id,
                    "thumb": "",
                    # set title to side_nav_title if available
                    "title": getattr(root, "side_nav_title", root_title),
                    "type": root_type,
                    "review_state": state,
                }
            )

        res["items"].extend(self.createNavTree())

        return res

    def recurse(self, children, level, bottomLevel):
        """Recurse through the navigation tree"""
        res = []

        show_thumbs = not self.data.no_thumbs
        show_icons = not self.data.no_icons

        thumb_scale = self.thumb_scale()

        for node in children:
            brain = node["item"]

            icon = ""

            if show_icons:
                if node["portal_type"] == "File":
                    icon = self.getMimeTypeIcon(node)

            has_thumb = brain.getIcon
            thumb = ""

            if show_thumbs and has_thumb and thumb_scale:
                thumb = "{}/@@images/image/{}".format(
                    node["item"].getURL(), thumb_scale
                )

            show_children = node["show_children"]
            item_remote_url = node["getRemoteUrl"]
            use_remote_url = node["useRemoteUrl"]
            item_url = node["getURL"]
            item = {
                "@id": item_url,
                "description": node["Description"],
                "href": item_remote_url if use_remote_url else item_url,
                "icon": icon,
                "is_current": node["currentItem"],
                "is_folderish": node["show_children"],
                "is_in_path": node["currentParent"],
                "items": [],
                "normalized_id": node["normalized_id"],
                "review_state": node["review_state"] or "",
                "thumb": thumb,
                "title": node.get("side_nav_title", node["Title"]),
                "type": node["normalized_portal_type"],
            }

            if node.get("nav_title", False):
                item.update({"title": node["nav_title"]})

            if node.get("side_nav_title", False):
                item.update({"side_nav_title": node["side_nav_title"]})

            nodechildren = node["children"]

            if (nodechildren and show_children and
                    ((level <= bottomLevel) or (bottomLevel == 0))):
                item["items"] = self.recurse(
                    nodechildren, level=level + 1, bottomLevel=bottomLevel
                )

            res.append(item)

        return res


@implementer(IExpandableElement)
@adapter(Interface, IPloneRestapiLayer)
class EEAContextNavigation:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand=False, prefix="expand.contextnavigation."):
        result = {
            "contextnavigation": {
                "@id": f"{self.context.absolute_url()}/@contextnavigation"
            }
        }
        if not expand:
            return result
        print("REQUEST FORM", self.request.form)
        data = eea_extract_data(IEEANavigationPortlet, self.request.form, prefix)
        renderer = EEANavigationPortletRenderer(self.context, self.request, data)
        res = renderer.render()
        result["contextnavigation"].update(res)
        return result

    def getNavTree(self):
        """ getNavTree"""
        # compatibility method with NavigationPortletRenderer, only for tests
        return self.__call__(expand=True)["contextnavigation"]


class EEAContextNavigationGet(original_get.ContextNavigationGet):
    """Custom ContextNavigationGet for context navigation"""
    def reply(self):
        """Reply with context navigation"""
        navigation = EEAContextNavigation(self.context, self.request)
        return navigation(expand=True, prefix="expand.contextnavigation.")[
            "contextnavigation"
        ]


class EEANavtreeStrategy(original_get.NavtreeStrategy):
    """Custom NavtreeStrategy for context navigation"""

    def decoratorFactory(self, node):
        """Decorate the navigation tree"""
        new_node = super().decoratorFactory(node)
        if getattr(new_node["item"], "side_nav_title", False):
            new_node["side_nav_title"] = new_node["item"].side_nav_title
        # Add any additional custom logic here
        return new_node


# Monkey patch the original NavtreeStrategy
original_get.NavtreeStrategy = EEANavtreeStrategy