import logging
import transaction
from plone.restapi.blocks import visit_blocks
from zope.lifecycleevent import modified
from xml.etree import ElementTree as ET
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter
from plone.namedfile.utils import getImageInfo
from zope.lifecycleevent import modified

logger = logging.getLogger("upgrade_svgs")
logger.setLevel(logging.INFO)


def upgrade_svgs(portal):
    """Upgrade SVG dimensions"""
    i = 0
    for brain in portal.portal_catalog():
        obj = brain.getObject()
        if (
            hasattr(obj, "image") and hasattr(obj.image, "_width") and hasattr(obj.image, "_height")
        ):
            logger.info("Processing %s", obj.absolute_url())
            contentType, width, height = getImageInfo(obj.image.data)
            if contentType == "image/svg+xml":
                obj.image._width = width
                obj.image._height = height
                modified(obj.image)
                i += 1
        if (
            hasattr(obj, "preview_image") and hasattr(obj.preview_image, "_width") and hasattr(obj.preview_image, "_height")
        ):
            logger.info("Processing %s", obj.absolute_url())
            contentType, width, height = getImageInfo(obj.preview_image.data)
            if contentType == "image/svg+xml":
                obj.preview_image._width = width
                obj.preview_image._height = height
                modified(obj.preview_image)
                i += 1
        if not i % 100:
            logger.info(i)
            transaction.commit()
    transaction.commit()
