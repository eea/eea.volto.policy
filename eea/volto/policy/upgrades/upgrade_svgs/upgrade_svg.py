"""Upgrade step for svgs to fix width and height"""

import logging
import transaction
from plone.namedfile.utils import getImageInfo
from zope.lifecycleevent import modified
from zope.annotation.interfaces import IAnnotations

logger = logging.getLogger("upgrade_svgs")
logger.setLevel(logging.INFO)


def upgrade_svgs(portal):
    """Upgrade SVG dimensions"""
    i = 0
    brains = portal.portal_catalog()
    total = len(brains)
    for idx, brain in enumerate(brains):
        obj = dict()
        try:
            obj = brain.getObject()
        except Exception:
            continue  # Skip to the next item if there's an error

        if (
            hasattr(obj, "image")
            and hasattr(obj.image, "_width")
            and hasattr(obj.image, "_height")
        ):

            contentType, width, height = getImageInfo(obj.image.data)
            if contentType == "image/svg+xml":
                logger.info("Processing %s", obj.absolute_url())
                obj.image._width = width
                obj.image._height = height
                anno = IAnnotations(obj)
                if "plone.scale" in anno:
                    del anno["plone.scale"]
                modified(obj)
                i += 1
        if (
            hasattr(obj, "preview_image")
            and hasattr(obj.preview_image, "_width")
            and hasattr(obj.preview_image, "_height")
        ):
            contentType, width, height = getImageInfo(obj.preview_image.data)
            if contentType == "image/svg+xml":
                logger.info("Processing %s", obj.absolute_url())
                obj.preview_image._width = width
                obj.preview_image._height = height
                anno = IAnnotations(obj)
                if "plone.scale" in anno:
                    del anno["plone.scale"]
                modified(obj)
                i += 1
        if not i % 100:
            logger.warning("Progress %s/%s", idx, total)
            logger.warning("Modified %s items", i)
            transaction.commit()
    transaction.commit()
