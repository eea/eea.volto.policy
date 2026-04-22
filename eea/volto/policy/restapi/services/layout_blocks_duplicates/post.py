"""POST @layout-blocks-duplicates endpoint.

Rewrites duplicate block UUIDs in stored blocks so every UUID is unique
within a content item. Mirrors the GET filters (``path``, ``portal_type``)
and rescans each object — does not trust client-supplied UUID lists.

Supports ``dry_run=1`` to report planned rewrites without persisting.
"""

import copy
import logging

from AccessControl import Unauthorized
from Acquisition import aq_base
from ZODB.POSException import ConflictError
from plone.protect.interfaces import IDisableCSRFProtection
from plone.restapi.batching import HypermediaBatch
from plone.restapi.services import Service
from zope.interface import alsoProvides
from zope.lifecycleevent import modified

from .utils import rewrite_duplicates

logger = logging.getLogger(__name__)


def _truthy(value):
    return str(value).lower() in ("1", "true", "yes", "on")


class LayoutBlocksDuplicatesPost(Service):
    """POST @layout-blocks-duplicates — rewrite duplicate block UUIDs."""

    def reply(self):
        # Disable plone.protect CSRF auto-check. Auth handled by the REST
        # API layer (token / basic). Without this the transformIterable
        # hook aborts the transaction, reverting every write.
        alsoProvides(self.request, IDisableCSRFProtection)

        catalog = self.context.portal_catalog
        query = {"object_provides": "plone.restapi.behaviors.IBlocks"}

        path = self.request.form.get("path")
        if path:
            query["path"] = path

        portal_type = self.request.form.get("portal_type")
        if portal_type:
            query["portal_type"] = portal_type

        dry_run = _truthy(self.request.form.get("dry_run", "0"))

        brains = catalog(**query)
        batch = HypermediaBatch(self.request, brains)

        items = []
        for brain in batch:
            try:
                obj = brain.getObject()
            except (Unauthorized, KeyError, AttributeError):
                continue
            except ConflictError:
                raise
            except Exception:
                logger.exception("Error loading %s", brain.getPath())
                continue

            base = aq_base(obj)
            blocks = getattr(base, "blocks", None)
            blocks_layout = getattr(base, "blocks_layout", None)
            if not blocks or not blocks_layout:
                continue

            if dry_run:
                # Work on copies so the live object is never mutated.
                target_blocks = copy.deepcopy(blocks)
                target_layout = copy.deepcopy(blocks_layout)
            else:
                target_blocks = blocks
                target_layout = blocks_layout

            rewrites = rewrite_duplicates(target_blocks, target_layout)
            if not rewrites:
                continue

            if not dry_run:
                # Write through the acquisition-wrapped object so behavior
                # descriptors (if any) run their setters. aq_base strips
                # that and may stash the attribute on the instance dict
                # while real storage lives in annotations.
                obj.blocks = target_blocks
                obj.blocks_layout = target_layout
                obj._p_changed = 1
                modified(obj)
                logger.info(
                    "layout-blocks-duplicates: rewrote %d uuids on %s",
                    len(rewrites),
                    brain.getPath(),
                )

            items.append(
                {
                    "@id": obj.absolute_url(),
                    "uid": brain.UID,
                    "title": brain.Title,
                    "portal_type": brain.portal_type,
                    "rewrites": rewrites,
                    "rewrites_count": len(rewrites),
                }
            )

        result = {
            "@id": batch.canonical_url,
            "dry_run": dry_run,
            "items_total": batch.items_total,
            "items_affected": len(items),
            "items": items,
        }
        links = batch.links
        if links:
            result["batching"] = links
        return result
