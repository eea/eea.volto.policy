"""
Serializers and Deserializers for the blocks of the EEA
"""

import copy
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from plone import api
from plone.app.contenttypes.interfaces import IImage
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import (
    IBlockFieldDeserializationTransformer,
    IBlockFieldSerializationTransformer,
)
from plone.restapi.serializer.blocks import (
    SlateBlockSerializerBase,
    uid_to_url,
)
from plone.restapi.deserializer.utils import path2uid
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest
from eea.volto.policy.restapi.services.contextnavigation.get import (
    EEANavigationPortletRenderer,
    eea_extract_data,
    IEEANavigationPortlet,
)
from eea.volto.policy.restapi.url_normalizer import (
    normalize_html_attribute_url,
    normalize_url_fields,
    strip_internal_url_prefix,
)

try:
    from eea.api.versions.browser.relations import EEAVersionsView
except ImportError:
    EEAVersionsView = None


def getLink(path):
    """
    Get link
    """

    URL = urlparse(path)

    if URL.netloc.startswith("localhost") and URL.scheme:
        return path.replace(URL.scheme + "://" + URL.netloc, "")
    return path


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class InternalURLPrefixDeserializationTransformer:
    """Strip configured internal backend URL prefixes before resolveuid transform."""

    order = 0
    block_type = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        return normalize_url_fields(value)


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class InternalURLPrefixSerializationTransformer:
    """Strip configured internal backend URL prefixes after block serialization."""

    order = 10000
    block_type = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        return normalize_url_fields(value)


def _safe_relative_path(path):
    """Return a traversal-safe portal-relative path or ``None``."""
    path = path.split("?", 1)[0].split("#", 1)[0]
    for suffix in ("/@@download/image", "/@@images/image"):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if not segments or any(
        segment in (".", "..") or segment.startswith("@") for segment in segments
    ):
        return None
    return "/".join(segments)


def resolve_internal_image(context, value):
    """Resolve a stored internal image reference without network access."""
    if not isinstance(value, str) or not value:
        return None

    normalized = strip_internal_url_prefix(value)
    parsed = urlparse(normalized)
    portal = None

    if parsed.scheme or parsed.netloc:
        try:
            portal = api.portal.get()
            portal_url = portal.absolute_url().rstrip("/")
        except Exception:
            return None
        if normalized == portal_url:
            normalized = "/"
        elif normalized.startswith(portal_url + "/"):
            normalized = normalized[len(portal_url) :]
        else:
            return None

    path = urlparse(normalized).path
    marker = "resolveuid/"
    if marker in path:
        uid = path.split(marker, 1)[1].split("/", 1)[0]
        if not uid or not uid.replace("-", "").isalnum():
            return None
        try:
            target = api.content.get(UID=uid)
        except Exception:
            return None
    else:
        relative = _safe_relative_path(path)
        if relative is None:
            return None
        try:
            portal = portal or api.portal.get()
            portal_id = getattr(portal, "getId", lambda: "")()
            if portal_id and relative.startswith(portal_id + "/"):
                relative = relative[len(portal_id) + 1 :]
            target = portal.restrictedTraverse(relative)
        except Exception:
            return None

    if target is None or not IImage.providedBy(target):
        return None
    return target


def _normalized_alt(value):
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _composed_metadata(title, description):
    if title and description:
        return f"{title}: {description}"
    return title or description or ""


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class ImageBlockSerializationTransformer:
    """Expose permission-safe live Image metadata and infer legacy alt source."""

    # Must inspect stored resolveuid values before RESTAPI's order-1 resolver.
    order = 0
    block_type = "image"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        block = copy.deepcopy(value)
        # Treat these keys as transient even if older or direct API writes managed
        # to persist them. Re-add them only after resolving and permission-checking.
        block.pop("image_title", None)
        block.pop("image_description", None)
        block.pop("image_metadata", None)
        target = resolve_internal_image(self.context, block.get("url"))
        if target is None or not IImage.providedBy(target):
            return block
        if not api.user.has_permission("View", obj=target):
            return block

        title = str(getattr(target, "title", "") or "").strip()
        description = str(getattr(target, "description", "") or "").strip()
        metadata = _composed_metadata(title, description)
        if not metadata:
            return block
        block["image_title"] = title
        block["image_description"] = description
        block["image_metadata"] = metadata

        source = block.get("alt_source")
        if source not in ("image-metadata", "custom"):
            alt = _normalized_alt(block.get("alt"))
            if not alt or alt == _normalized_alt(metadata):
                source = "image-metadata"
            else:
                source = "custom"
            block["alt_source"] = source

        if source == "image-metadata":
            block["alt"] = ""
        return block


@implementer(IBlockFieldDeserializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class ImageBlockDeserializationTransformer:
    """Prevent transient live Image metadata from being persisted in blocks."""

    order = 0
    block_type = "image"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        block = copy.deepcopy(value)
        block.pop("image_title", None)
        block.pop("image_description", None)
        block.pop("image_metadata", None)
        return block


class HTMLBlockDeserializerBase:
    """
    HTML block Deserializer for the hrefs and src
    """

    order = 9999
    block_type = "html"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _clean_download_image(self, url: str) -> str:
        """
        Remove /@@download/image
        """
        return url.replace("/@@download/image", "")

    def __call__(self, block):
        raw_html = block.get("html", "")
        if not raw_html:
            return block

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")

        # Resolve all <a> and <img> tags to UIDs
        for tag in soup.find_all(["a", "img"]):
            if tag.name == "a" and tag.has_attr("href"):
                tag["href"] = self._clean_download_image(tag["href"])
                tag["href"] = normalize_html_attribute_url(tag["href"])
                tag["href"] = path2uid(context=self.context, link=tag["href"])

            elif tag.name == "img" and tag.has_attr("src"):
                tag["src"] = self._clean_download_image(tag["src"])
                tag["src"] = normalize_html_attribute_url(tag["src"])
                tag["src"] = path2uid(context=self.context, link=tag["src"])

        # Serialize the modified HTML back into the block
        block["html"] = str(soup)

        return block


class HTMLBlockSerializerBase:
    """
    HTML block Serializer for the hrefs and src
    """

    order = 9999
    block_type = "html"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, block):
        block_serializer = copy.deepcopy(block)
        raw_html = block_serializer.get("html", "")

        if not raw_html:
            return block

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")
        # Resolve all <a> and <img> tags
        for tag in soup.find_all(["a", "img"]):
            if tag.name == "a" and tag.has_attr("href"):
                tag["href"] = self._resolve_uid(tag["href"])
            elif tag.name == "img" and tag.has_attr("src"):
                tag["src"] = self._resolve_uid(tag["src"], is_image=True)

        # Serialize the modified HTML back into the block
        block_serializer["html"] = str(soup)
        return block_serializer

    def _resolve_uid(self, url, is_image=False):
        """
        Convert resolve UID URLs into relative links.
        If the URL points to an image, append /@@download/image.
        """
        if "/resolveuid/" in url:
            resolved_url = uid_to_url(url)
            if is_image and "/resolveuid/" not in resolved_url:
                return strip_internal_url_prefix(f"{resolved_url}/@@download/image")
            return strip_internal_url_prefix(resolved_url or url)
        return strip_internal_url_prefix(url)


class SlateBlockSerializer(SlateBlockSerializerBase):
    """SlateBlockSerializerBase."""

    block_type = "slate"

    def handle_img(self, child):
        "Serializer for the imgs"
        if child.get("url"):
            if "resolveuid/" in child["url"]:
                url = uid_to_url(child["url"])
                if "resolveuid/" not in url:
                    url = "%s/@@download/image" % url
                child["url"] = strip_internal_url_prefix(url)


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class RestrictedBlockSerializationTransformer:
    """Enhanced Restricted Block serialization with allow or deny logic"""

    order = 9999
    block_type = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        # Check if this is a restricted block
        restricted_block = value.get("restrictedBlock", False)
        if not restricted_block:
            return value
        # editors in context can see
        if api.user.has_permission("Modify portal content", obj=self.context):
            return value

        # First check: User MUST have the manage permission to see any
        # restricted block
        if (
            not api.user.has_permission(
                "EEA: Manage restricted blocks", obj=self.context
            )
            and not value.get("deny_view")
            and not value.get("allow_view")
        ):
            return {"@type": "empty"}

        # Get current user (we know they have the basic permission)
        current_user = api.user.get_current()
        deny_view = value.get("deny_view", [])

        if deny_view:
            # If deny_view is set, users in the list can't see
            if self._check_user_access(current_user, deny_view):
                return {"@type": "empty"}

        # Check allow_view permissions
        allow_view = value.get("allow_view", [])
        if allow_view:
            # If allow_view is set, only users in the list can see
            if not self._check_user_access(current_user, allow_view):
                return {"@type": "empty"}
        return value

    def _check_user_access(self, current_user, access_list):
        """
        Check if current user has access based on allow/deny list

        Args:
            current_user: Current Plone user object
            access_list: List of users/groups with access permissions

        Returns:
            bool: True if user has access, False otherwise
        """
        current_user_id = current_user.getId()

        # Get user's groups
        user_groups = api.group.get_groups(user=current_user)
        user_group_ids = [group.getId() for group in user_groups]

        for access_item in access_list:
            access_type = access_item.get("type", "")
            access_id = access_item.get("id", "")

            if access_type == "user":
                # For users, check by ID (the primary identifier)
                if access_id == current_user_id:
                    return True

            elif access_type == "group":
                # For groups, check by ID (the primary identifier)
                if access_id in user_group_ids:
                    return True

        return False

    def _get_user_groups(self, user):
        """
        Helper method to get all groups a user belongs to

        Args:
            user: Plone user object

        Returns:
            list: List of group IDs the user belongs to
        """
        try:
            groups = api.group.get_groups(user=user)
            return [group.getId() for group in groups]
        except Exception:
            return []


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class ContextNavigationBlockSerializationTransformer:
    """ContextNavigation Block serialization"""

    order = 9999
    block_type = "contextNavigation"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        if value.get("variation", None) == "report_navigation":
            if (
                "root_node" in value
                and isinstance(value["root_node"], list)
                and len(value["root_node"]) > 0
            ):
                root_nav_item = value["root_node"][0]
                url = urlparse(root_nav_item.get("@id", ""))
                value["root_path"] = url.path

            data = eea_extract_data(IEEANavigationPortlet, value, prefix=None)

            renderer = EEANavigationPortletRenderer(self.context, self.request, data)
            res = renderer.render()
            is_data_available = res.get("available", True)  # or get res[items]?
            value["results"] = is_data_available

        return value


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class AllVersionBlockSerializationTransformer:
    """All versions Block serialization"""

    order = 9999
    block_type = "eea_versions"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        if value.get("@type", None) == "eea_versions":
            all_versions = EEAVersionsView(self.context, self.request)
            results = all_versions.newer_versions() or all_versions.older_versions()

            value["results"] = len(results) > 0
        return value


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class LatestVersionBlockSerializationTransformer:
    """Latest versions Block serialization"""

    order = 9999
    block_type = "eea_latest_version"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        if value.get("@type", None) == "eea_latest_version":
            all_versions = EEAVersionsView(self.context, self.request)
            results = all_versions.newer_versions()

            value["results"] = len(results) > 0

        return value
