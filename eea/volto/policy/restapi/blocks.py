from urllib.parse import urlparse
from plone import api
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest
from bs4 import BeautifulSoup
from plone.restapi.serializer.blocks import (
    SlateBlockSerializerBase,
    uid_to_url,
)
from plone.restapi.deserializer.utils import path2uid
import copy


def getLink(path):
    """
    Get link
    """

    URL = urlparse(path)

    if URL.netloc.startswith("localhost") and URL.scheme:
        return path.replace(URL.scheme + "://" + URL.netloc, "")
    return path


class HTMLBlockDeserializerBase:
    order = 100
    block_type = "html"

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, block):
        raw_html = block.get("html", "")

        if not raw_html:
            return block

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")

        # Resolve all <a> and <img> tags to UIDs
        for tag in soup.find_all(["a", "img"]):
            if tag.name == "a" and tag.has_attr("href"):

                tag["href"] = path2uid(context=self.context, link=tag["href"])

            elif tag.name == "img" and tag.has_attr("src"):
                tag["src"] = path2uid(context=self.context, link=tag["src"])

        # Serialize the modified HTML back into the block
        block["html"] = str(soup)
        return block

    def _convert_to_uid(self, url, is_image=False):
        """
        Convert relative or absolute URLs into resolve UID links.
        """
        uid = path2uid(self.context, url)
        if uid:
            return f"/resolveuid/{uid}"
        return url


class HTMLBlockSerializerBase:
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
            if is_image and resolved_url:
                return f"{resolved_url}/@@download/image"
            return resolved_url or url
        return url


class SlateBlockSerializer(SlateBlockSerializerBase):
    """SlateBlockSerializerBase."""

    block_type = "slate"

    def handle_img(self, child):
        if child.get("url"):
            if "resolveuid" in child["url"]:
                url = uid_to_url(child["url"])
                url = "%s/@@download/image" % url
                child["url"] = url


@implementer(IBlockFieldSerializationTransformer)
@adapter(IBlocks, IBrowserRequest)
class RestrictedBlockSerializationTransformer:
    """Restricted Block serialization"""

    order = 9999
    block_type = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, value):
        restrictedBlock = value.get("restrictedBlock", False)
        if not restrictedBlock:
            return value
        if restrictedBlock and api.user.has_permission(
            "EEA: Manage restricted blocks", obj=self.context
        ):
            return value
        return {"@type": "empty"}