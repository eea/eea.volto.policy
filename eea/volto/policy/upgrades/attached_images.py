"""
Module for migrating image references in Volto blocks to the new
format. Contains functions to update image references in item,
teaser, and hero blocks.
"""
import logging
from urllib.parse import urlparse
import transaction

from plone.restapi.blocks import visit_blocks
from plone.restapi.deserializer.utils import path2uid
from zope.lifecycleevent import modified

logger = logging.getLogger("migrate_images")
logger.setLevel(logging.INFO)


def get_relative_url_path(url: str) -> str:
    """Return the site-relative path portion of *url*.

    If *url* is already a relative path it is returned unchanged,
    otherwise the network component is stripped. The returned value is
    always prefixed with a leading ``/`` so that it can be passed to
    :pyfunc:`plone.restapi.deserializer.utils.path2uid` directly.
    """
    if not url:
        return ""

    if 'resolveuid' in url:
        # If the URL is already a resolveuid link, return it as is.
        return url

    path = urlparse(url).path or url
    if not path.startswith("/"):
        path = f"/{path}"
    return path


def _migrate_block_images(
    portal,
    block_types: list,
    image_field: str,
    item_block_asset_type=None,
) -> str:
    """Core routine for migrating image references inside Volto blocks.

    Parameters
    ----------
    portal
        Plone portal object.
    block_types
        List of block ``@type`` values to process.
    image_field
        Name of the field inside the block that stores the image path.
    item_block_asset_type
        If given, the block must have ``assetType`` equal to this value.
    Returns
    -------
    str
        Number of Plone objects that were processed.
    """
    processed = 0
    for brain in portal.portal_catalog(
        object_provides="plone.restapi.behaviors.IBlocks",
        block_types=block_types,
    ):
        try:
            obj = brain.getObject()
        except Exception as e:
            logger.error("Failed to get object from brain: %s", e)
            continue
        blocks = obj.blocks
        logger.info("Processing %s", obj.absolute_url())

        changed = False
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type") in block_types and
                block.get(image_field) and
                isinstance(block[image_field], str) and (
                    item_block_asset_type is None or
                    block.get("assetType") == item_block_asset_type
                )
            ):
                rel_path = get_relative_url_path(block[image_field])
                uid = path2uid(context=obj, link=rel_path)
                if not uid:
                    logger.warning(
                        "Failed to resolve UID for path: %s", rel_path
                    )
                    continue
                block[image_field] = [
                    {
                        "@type": "Image",
                        "@id": uid,
                        "image_field": "image",
                    }
                ]
                changed = True

        if changed:
            obj.blocks = blocks
            modified(obj)
            processed += 1
        if not processed % 100:
            logger.info("Processed %d objects", processed)
            try:
                transaction.commit()
            except Exception as e:
                logger.error("Transaction commit failed: %s", e)
                transaction.abort()
                raise

    try:
        transaction.commit()
        logger.info(
            "Migration completed. Total objects processed: %d", processed)
        return f"{processed} objects processed"
    except Exception as e:
        logger.error("Final transaction commit failed: %s", e)
        transaction.abort()
        raise


def migrate_item_images(portal):
    """Migrate image references in Volto ``item`` blocks."""
    return _migrate_block_images(
        portal,
        block_types=["item"],
        image_field="image",
        item_block_asset_type="image",
    )


def migrate_teaser_images(portal):
    """Migrate image references in Volto ``teaser`` blocks."""
    return _migrate_block_images(
        portal,
        block_types=["teaser"],
        image_field="preview_image",
    )


def migrate_hero_images(portal):
    """Migrate image references in Volto ``hero`` blocks."""
    return _migrate_block_images(
        portal,
        block_types=["hero"],
        image_field="image",
    )
