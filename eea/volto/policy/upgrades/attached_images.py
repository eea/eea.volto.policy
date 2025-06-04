from plone.restapi.blocks import visit_blocks
from zope.lifecycleevent import modified

import logging
import transaction

from plone.restapi.deserializer.utils import path2uid

logger = logging.getLogger("migrate_images")
logger.setLevel(logging.INFO)


def migrate_item_images(portal):
    i = 0
    output = ""
    types = ["item"]
    for brain in portal.portal_catalog(
        object_provides="plone.restapi.behaviors.IBlocks",
        block_types=types
    ):
        obj = brain.getObject()
        blocks = obj.blocks
        logger.info(f"Processing {obj.absolute_url()}")
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type", False)
                and block["@type"] in types
                and block['assetType'] == "image"
                and block['image'] and type(block['image']) == str
            ):
                new_block = block.copy()
                logger.info(
                    f'{obj.absolute_url()} - Updated hero "image" '
                    f'field: {block["image"]}')

                uid = path2uid(context=obj, link=block["image"])
                if not uid:
                    logger.warning(
                        f"Failed to convert path to UID: {block['image']}")
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
            logger.info(f"Processed {i} objects")
            try:
                transaction.commit()
            except Exception as e:
                logger.error(f"Transaction commit failed: {e}")
                transaction.abort()
                raise

    try:
        transaction.commit()
        logger.info(
            f"Migration completed successfully. Total objects processed: {i}")
    except Exception as e:
        logger.error(f"Final transaction commit failed: {e}")
        transaction.abort()
        raise
    return output


def migrate_teaser_images(portal):
    i = 0
    output = ""
    types = ["teaser"]
    for brain in portal.portal_catalog(
        object_provides="plone.restapi.behaviors.IBlocks",
        block_types=types
    ):
        obj = brain.getObject()
        blocks = obj.blocks
        logger.info(f"Processing {obj.absolute_url()}")
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type", False)
                and block["@type"] in types
                and block['preview_image']
                and type(block['preview_image']) == str
            ):
                new_block = block.copy()
                logger.info(
                    f'{obj.absolute_url()} - Updated teaser "preview_image" field: '
                    f'{block["preview_image"]}')

                image = [
                    {
                        "@type": "Image",
                        "@id": path2uid(context=obj, link=block["preview_image"]),
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
            logger.info(i)
            transaction.commit()
    transaction.commit()
    return output


def migrate_hero_images(portal):
    i = 0
    output = ""
    types = ["hero"]
    for brain in portal.portal_catalog(
        object_provides="plone.restapi.behaviors.IBlocks",
        block_types=types
    ):
        obj = brain.getObject()
        blocks = obj.blocks
        logger.info(f"Processing {obj.absolute_url()}")
        for block in visit_blocks(obj, blocks):
            if (
                block.get("@type", False)
                and block["@type"] in types
                and block['image']
                and type(block['image']) == str
            ):
                new_block = block.copy()
                logger.info(
                    f'{obj.absolute_url()} - Updated item "image" field: '
                    f'{block["image"]}')

                uid = path2uid(context=obj, link=block["image"])
                if not uid:
                    logger.warning(
                        f"Failed to convert path to UID: {block['image']}")
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
            logger.info(i)
            transaction.commit()
    transaction.commit()
    return output
