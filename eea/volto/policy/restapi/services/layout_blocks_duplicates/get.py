"""GET @layout-blocks-duplicates endpoint.

Lists content items whose stored blocks contain duplicate UUIDs
(the fingerprint of the layout-block copy/paste bug).
"""

import logging

from AccessControl import Unauthorized
from Acquisition import aq_base
from ZODB.POSException import ConflictError
from plone.restapi.batching import HypermediaBatch
from plone.restapi.services import Service

from .utils import find_duplicates

logger = logging.getLogger(__name__)


class LayoutBlocksDuplicatesGet(Service):
    """GET @layout-blocks-duplicates — scan content for duplicate block UUIDs."""

    def reply(self):
        catalog = self.context.portal_catalog
        query = {"object_provides": "plone.restapi.behaviors.IBlocks"}

        path = self.request.form.get("path")
        if path:
            query["path"] = path

        portal_type = self.request.form.get("portal_type")
        if portal_type:
            query["portal_type"] = portal_type

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

            duplicates = find_duplicates(blocks, blocks_layout)
            if not duplicates:
                continue

            items.append(
                {
                    "@id": obj.absolute_url(),
                    "uid": brain.UID,
                    "title": brain.Title,
                    "portal_type": brain.portal_type,
                    "duplicate_uuids": duplicates,
                }
            )

        result = {
            "@id": batch.canonical_url,
            "items_total": batch.items_total,
            "items_affected": len(items),
            "items": items,
        }
        links = batch.links
        if links:
            result["batching"] = links
        return result
