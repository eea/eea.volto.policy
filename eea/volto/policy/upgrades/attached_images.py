"""
Module for migrating image references in Volto blocks to the new
format. Contains functions to update image references in item,
teaser, and hero blocks.
"""
import logging
import transaction

from plone.restapi.blocks import visit_blocks
from plone.restapi.deserializer.utils import path2uid
from zope.lifecycleevent import modified

logger = logging.getLogger("migrate_images")
logger.setLevel(logging.INFO)


def migrate_item_images(portal):
    """
    Migrate image references in item blocks from string paths to
    object references.
    """
    i = 0
    output = ""
    types = ["item"]
    for brain in portal.portal_catalog(
        object_provides="plone.restapi.behaviors.IBlocks",
        block_types=types
    ):
        obj = brain.getObject()
        blocks = obj.blocks
        logger.info("Processing %s", obj.absolute_url())
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type", False) and
                block["@type"] in types and
                block['assetType'] == "image" and
                block['image'] and isinstance(block['image'], str)
            ):
                new_block = block.copy()
                logger.info(
                    '%s - Updated hero "image" field: %s',
                    obj.absolute_url(), block["image"]
                )

                uid = path2uid(context=obj, link=block["image"])
                if not uid:
                    logger.warning(
                        "Failed to convert path to UID: %s", block['image']
                    )
                    continue

                image = [
                    {
                        "@type": "Image",
                        "@id": uid,
                        "image_field": "image"
                    }
                ]
                new_block["image"] = image
                block.clear()
                block.update(new_block)

        obj.blocks = blocks
        modified(obj)
        i += 1
        if not i % 100:
            logger.info("Processed %d objects", i)
            try:
                transaction.commit()
            except Exception as e:
                logger.error("Transaction commit failed: %s", e)
                transaction.abort()
                raise

    try:
        transaction.commit()
        logger.info(
            "Migration completed successfully. Total objects processed: %d",
            i
        )
    except Exception as e:
        logger.error("Final transaction commit failed: %s", e)
        transaction.abort()
        raise
    return output


def migrate_teaser_images(portal):
    """
    Migrate image references in teaser blocks from string paths to
    object references.
    """
    i = 0
    output = ""
    types = ["teaser"]
    for brain in portal.portal_catalog(
        object_provides="plone.restapi.behaviors.IBlocks",
        block_types=types
    ):
        obj = brain.getObject()
        blocks = obj.blocks
        logger.info("Processing %s", obj.absolute_url())
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type", False) and
                block["@type"] in types and
                block['preview_image'] and
                isinstance(block['preview_image'], str)
            ):
                new_block = block.copy()
                logger.info(
                    '%s - Updated teaser "preview_image" field: %s',
                    obj.absolute_url(), block["preview_image"]
                )

                image = [
                    {
                        "@type": "Image",
                        "@id": path2uid(
                            context=obj, link=block["preview_image"]
                        ),
                        "image_field": "image"
                    }
                ]
                new_block["preview_image"] = image
                block.clear()
                block.update(new_block)

        obj.blocks = blocks
        modified(obj)
        i += 1
        if not i % 100:
            logger.info("%d", i)
            transaction.commit()
    transaction.commit()
    return output


def migrate_hero_images(portal):
    """
    Migrate image references in hero blocks from string paths to
    object references.
    """
    i = 0
    output = ""
    types = ["hero"]
    for brain in portal.portal_catalog(
            object_provides="plone.restapi.behaviors.IBlocks",
            block_types=types
    ):
        obj = brain.getObject()
        blocks = obj.blocks
        logger.info("Processing %s", obj.absolute_url())
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type", False) and
                block["@type"] in types and
                block['image'] and
                isinstance(block['image'], str)
            ):
                new_block = block.copy()
                logger.info(
                    '%s - Updated item "image" field: %s',
                    obj.absolute_url(), block["image"]
                )

                uid = path2uid(context=obj, link=block["image"])
                if not uid:
                    logger.warning(
                        "Failed to convert path to UID: %s", block['image']
                    )
                    continue

                image = [
                    {
                        "@type": "Image",
                        "@id": uid,
                        "image_field": "image"
                    }
                ]
                new_block["image"] = image
                block.clear()
                block.update(new_block)

        obj.blocks = blocks
        modified(obj)
        i += 1
        if not i % 100:
            logger.info("%d", i)
            transaction.commit()
    transaction.commit()
    return output
