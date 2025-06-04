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
                logger.info(f'{obj.absolute_url()} - Updated item "image" field: {block["image"]}')

                image = [
                    {
                        "@type": "Image",
                        "@id": path2uid(context=obj, link=block["image"]),
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
                logger.info(f'{obj.absolute_url()} - Updated item "image" field: {block["preview_image"]}')

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
                logger.info(f'{obj.absolute_url()} - Updated item "image" field: {block["image"]}')

                image = [
                    {
                        "@type": "Image",
                        "@id": path2uid(context=obj, link=block["image"]),
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