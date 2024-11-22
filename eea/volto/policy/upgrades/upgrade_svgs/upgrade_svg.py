"""Upgrade step for svgs to fix width and height"""
import transaction
from plone.namedfile.utils import getImageInfo
from zope.lifecycleevent import modified
from zope.annotation.interfaces import IAnnotations
from Products.ZCatalog.ProgressHandler import ZLogHandler


def upgrade_svgs(portal):
    """Upgrade SVG dimensions"""

    i = 0
    brains = portal.portal_catalog()
    pghandler = ZLogHandler(100)
    pghandler.init("Recalculate svgs width and height", len(brains))
    for idx, brain in enumerate(brains):
        pghandler.report(idx)
        obj = dict()
        try:
            obj = brain.getObject()
        except Exception:
            continue  # Skip to the next item if there's an error

        # Process the main image only if dimensions are less than 5
        if (
            hasattr(obj, "image") and
            hasattr(obj.image, "_width") and
            hasattr(obj.image, "_height") and
            (obj.image._width < 5 or obj.image._height < 5)
        ):
            contentType, width, height = getImageInfo(obj.image.data)
            if contentType == "image/svg+xml":
                obj.image._width = width
                obj.image._height = height
                anno = IAnnotations(obj)
                if "plone.scale" in anno:
                    del anno["plone.scale"]
                modified(obj)
                i += 1

        # Process the preview image only if dimensions are less than 5
        if (
            hasattr(obj, "preview_image") and
            hasattr(obj.preview_image, "_width") and
            hasattr(obj.preview_image, "_height") and
            (obj.preview_image._width < 5 or obj.preview_image._height < 5)
        ):
            contentType, width, height = getImageInfo(obj.preview_image.data)
            if contentType == "image/svg+xml":
                obj.preview_image._width = width
                obj.preview_image._height = height
                anno = IAnnotations(obj)
                if "plone.scale" in anno:
                    del anno["plone.scale"]
                modified(obj)
                i += 1

        if not i % 100:
            transaction.commit()
    pghandler.finish()
    transaction.commit()
