""" Migrate image references in Volto blocks to the new format.
"""
import json
import logging

from Products.Five.browser import BrowserView

try:
    from plone import api  # type: ignore
    _HAS_API = True
except Exception:  # pragma: no cover
    _HAS_API = False

from eea.volto.policy.upgrades.attached_images import (
    _migrate_block_images,
)

logger = logging.getLogger("eea.volto.policy.image_migrate")


class ImageMigrateContent(BrowserView):
    """Run image migration for Volto blocks outside of the ones defined
    in the upgrade step (hero, teaser, item)

    Usage examples::

        @@image-migrate?block_type=item&field_name=image
        @@image-migrate?block_type=teaser&field_name=preview_image
        @@image-migrate?block_type=hero,item&field_name=image
        @@image-migrate?block_type=item&field_name=image

    - Query params:
        * block_type: comma-separated list of block @types (required)
        * field_name: name of image field inside the block (required)
    """

    def _json(self, data, status=200):
        """Return JSON response"""
        self.request.response.setHeader("Content-Type", "application/json")
        self.request.response.setStatus(status)
        return json.dumps(data)

    def __call__(self):
        req = self.request

        block_types_param = req.get("block_type")
        field_name = req.get("field_name")

        if not block_types_param or not field_name:
            return self._json(
                {
                    "error": "Required parameters: 'block_type' & 'field_name'",
                },
                status=400,
            )

        block_types = [t.strip()
                       for t in block_types_param.split(",") if t.strip()]

        # Get the portal
        if _HAS_API:
            portal = api.portal.get()
        else:  # pragma: no cover
            portal = self.context.portal_url.getPortalObject()

        try:
            processed_msg = _migrate_block_images(
                portal,
                block_types=block_types,
                image_field=field_name,
            )
        except Exception as e:  # pragma: no cover
            logger.exception("Image migration failed")
            return self._json({"error": f"Migration failed: {e}"}, status=500)

        return self._json(
            {
                "status": "ok",
                "message": processed_msg,
                "block_types": block_types,
                "field_name": field_name,
            }
        )
