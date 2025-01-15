""" block-related utils """

from plone import api
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from zope.component import adapter
from zope.interface import implementer
from zope.publisher.interfaces.browser import IBrowserRequest
from copy import deepcopy

from lxml.html import fragments_fromstring, tostring
from plone import api
from plone.api import portal
from plone.app.textfield.interfaces import IRichText
from plone.dexterity.interfaces import IDexterityContainer, IDexterityContent
from plone.restapi.behaviors import IBlocks
from plone.restapi.interfaces import IBlockFieldSerializationTransformer
from plone.restapi.serializer.blocks import SlateBlockSerializerBase, uid_to_url
from plone.restapi.serializer.converters import json_compatible
from plone.restapi.serializer.dxcontent import SerializeFolderToJson, SerializeToJson
from plone.restapi.serializer.dxfields import DefaultFieldSerializer
from zope.component import adapter, getMultiAdapter
from zope.interface import Interface, implementer

from bs4 import BeautifulSoup
from plone.restapi.serializer.utils import uid_to_url

class HTMLBlockSerializerBase:
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

        # Resolve all <a> and <img> tags
        for tag in soup.find_all(['a', 'img']):
            if tag.name == "a" and tag.has_attr("href"):
                tag["href"] = self._resolve_uid(tag["href"])
            elif tag.name == "img" and tag.has_attr("src"):
                tag["src"] = self._resolve_uid(tag["src"], is_image=True)

        # Serialize the modified HTML back into the block
        block["html"] = str(soup)
        return block

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

    block_type="slate"

    def handle_img(self, child):
        if child.get("url"):
            url = uid_to_url(child["url"])
            if child.get("scale"):
                url = "%s/@@images/image/%s" % (url, child["scale"])
            else:
                url = "%s/@@images/image/huge" % url

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
                'EEA: Manage restricted blocks', obj=self.context):
            return value
        return {
            "@type": "empty"
        }



