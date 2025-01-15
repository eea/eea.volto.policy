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