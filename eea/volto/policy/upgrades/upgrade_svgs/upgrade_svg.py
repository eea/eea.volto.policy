"""Upgrade step for svgs to fix width and height"""

import transaction
from plone.namedfile.utils import getImageInfo
from zope.lifecycleevent import modified
from zope.annotation.interfaces import IAnnotations
from Products.ZCatalog.ProgressHandler import ZLogHandler


def upgrade_svgs(portal):
    """Upgrade SVG dimensions with intermediate commits"""

    brains = portal.portal_catalog()
    batch_size = 30
    total_brains = len(brains)
    pghandler = ZLogHandler(100)
    pghandler.init("Recalculate svgs width and height", total_brains)

    updated_count = 0  # Tracks number of updates
    for idx, brain in enumerate(brains):
        obj = dict()
        pghandler.report(idx)
        try:
            obj = brain.getObject()
        except Exception:
            continue  # Skip object if it cannot be retrieved

        def process_image(image_attr):
            """Process an image field if it's an SVG and needs updating."""
            image = getattr(obj, image_attr, None)
            if (
                image
                and hasattr(image, "_width")
                and hasattr(image, "_height")
                and (
                    image._width < 5 or image._height < 5
                )  # Skip already upgraded images
            ):
                contentType, width, height = getImageInfo(image.data)
                if contentType == "image/svg+xml":
                    image._width = width
                    image._height = height
                    anno = IAnnotations(obj)
                    if "plone.scale" in anno:
                        del anno["plone.scale"]
                    modified(obj)
                    return True
            return False

        # Process both main and preview images
        updated = process_image("image") or process_image("preview_image")
        if updated:
            updated_count += 1

        # Commit transaction every batch_size updates
        if updated_count and updated_count % batch_size == 0:
            transaction.commit()

    pghandler.finish()
    transaction.commit()
