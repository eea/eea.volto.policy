""" Migrate teaser block from teaserGrid to Volto 17 gridBlock
"""
# pylint: disable=line-too-long
import copy
import logging
import transaction
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage
from plone.base.interfaces.siteroot import IPloneSiteRoot
from plone import api
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.blocks import visit_blocks
from plone.restapi.types.utils import update_field, get_info_for_field
from plone.restapi.types.utils import serializeSchema
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.lifecycleevent import modified
from zExceptions import Forbidden
logger = logging.getLogger("eea.volto.policy")


class TeaserMigrateContent(BrowserView):
    """Migration of teaserGrid to gridBlock"""

    def convert(self, block_data):
        """Convert block_data to gridBlock"""
        grid_block = copy.deepcopy(block_data)

        grid_block["@type"] = "gridBlock"
        columns = block_data.get("columns", [])
        grid_block["blocks_layout"] = {
            "items": [column["id"] for column in columns]
        }
        grid_block["blocks"] = {x["id"]: x for x in columns}
        try:
            del grid_block["columns"]
        except KeyError:
            logger.exception("No columns found in %s",
                             self.context.absolute_url())
        return grid_block

    def migrate(self):
        """Migrate teaserGrid to gridBlock"""
        count = 0
        blocks = getattr(self.context, "blocks", {})
        for block in visit_blocks(self.context, blocks):
            # we have found a teaserGrid
            if block.get("@type", False) and block["@type"] == "teaserGrid":
                new_block = self.convert(block)
                block.clear()
                block.update(new_block)
                count += 1
        if count:
            logger.info(
                "Migrated %s teaserBlock to gridBlock for %s",
                count,
                self.context.absolute_url(),
            )
            modified(self.context)
        return count

    def __call__(self):
        # Disable CSRF protection
        alsoProvides(self.request, IDisableCSRFProtection)
        count = self.migrate()
        IStatusMessage(self.request).addStatusMessage(
            f"Migrated {count} Teaser Blocks")
        return self.request.response.redirect(self.context.absolute_url())


class TeaserMigrateSite(TeaserMigrateContent):
    """Migrate Teaser Blocks to Volto 17"""

    def migrate(self):
        """Migrate Teaser Blocks to Volto 17"""
        brains = api.content.find(
            context=self.context,
            object_provides="plone.restapi.behaviors.IBlocks"
        )

        count = 0
        total = len(brains)
        for idx, brain in enumerate(brains):
            obj = brain.getObject()
            if IPloneSiteRoot.providedBy(obj):
                if super().migrate():
                    count += 1
                continue
            view = queryMultiAdapter(
                (obj, self.request), name="teaser-migrate")
            if view.migrate():
                count += 1
            if idx % 100 == 0:
                transaction.savepoint(optimistic=True)
                logger.info("Progress %s of %s. Migrated %s",
                            idx, total, count)
        return count

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        count = self.migrate()
        IStatusMessage(self.request).addStatusMessage(
            f"Migrated {count} Teaser Blocks"
        )
        return self.request.response.redirect(self.context.absolute_url())


class TeaserMigrateLayout(TeaserMigrateSite):
    """ Migrate Teaser Blocks in DX Layout """

    def migrate_type(self, context):
        """Migrate teaserGrid to gridBlock"""
        count = 0
        try:
            blocks = get_info_for_field(context, self.request, "blocks")
        except (AttributeError, Forbidden):
            # no blocks field
            return count
        else:
            blocks = blocks.get("default", {})

        for block in visit_blocks(context, blocks):
            # we have found a teaserGrid
            if block.get("@type", False) and block["@type"] == "teaserGrid":
                new_block = self.convert(block)
                block.clear()
                block.update(new_block)
                count += 1
        if count:
            update_field(context, self.request, {
                "id": "blocks",
                "default": blocks,
            })
            serializeSchema(context.schema)
        return count

    def migrate(self):
        """ Migrate Teaser Blocks in DX Layout """
        count = 0
        ctypes = queryUtility(
            IVocabularyFactory,
            name="plone.app.vocabularies.ReallyUserFriendlyTypes"
        )
        dtool = queryMultiAdapter(
            (self.context, self.request), name="dexterity-types")
        brains = ctypes(self.context)
        total = len(brains)
        for idx, ctype in enumerate(brains):
            cid = ctype.value
            try:
                dtype = dtool.publishTraverse(self.request, cid)
            except KeyError as err:
                # KeyError: 'Discussion Item'
                logger.exception(err)
                continue
            try:
                if self.migrate_type(dtype):
                    count += 1
            except AttributeError as err:
                logger.exception("Could not migrate %s: %s", cid, err)
            logger.info("Progress %s of %s. Migrated %s", idx, total, count)
        return count

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        count = self.migrate()
        IStatusMessage(self.request).addStatusMessage(
            f"Migrated content-types layout {count} teaserGrid to gridBlock"
        )
        return self.request.response.redirect(self.context.absolute_url())
