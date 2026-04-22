"""
Utility functions for eea.volto.policy package.
"""

import re

from plone.app.uuid.utils import uuidToCatalogBrain
from plone.restapi.interfaces import IObjectPrimaryFieldTarget
from zope.component import queryMultiAdapter


# Compatibility import for resolve_uid function
try:
    from plone.restapi.serializer.utils import resolve_uid
except ImportError:
    # Fallback implementation for older plone.restapi versions (< 9.0)
    RESOLVEUID_RE = re.compile(r"^[./]*resolve[Uu]id/([^/]*)/?(.*)$")

    def resolve_uid(path):
        """Fallback implementation of resolve_uid for older plone.restapi
        versions.

        Resolves a resolveuid URL into a tuple of absolute URL and catalog
        brain.
        If the original path is not found (including external URLs), it
        will be returned unchanged and the brain will be None.

        Args:
            path (str): The path to resolve, potentially containing resolveuid

        Returns:
            tuple: (resolved_url, brain) where brain is the catalog brain or
            None
        """
        if not path:
            return "", None
        match = RESOLVEUID_RE.match(path)
        if match is None:
            return path, None

        uid, suffix = match.groups()
        brain = uuidToCatalogBrain(uid)
        if brain is None:
            return path, None
        href = brain.getURL()
        if suffix:
            return href + "/" + suffix, brain
        target_object = brain._unrestrictedGetObject()
        adapter = queryMultiAdapter(
            (target_object, target_object.REQUEST),
            IObjectPrimaryFieldTarget,
        )
        if adapter:
            a_href = adapter()
            if a_href:
                return a_href, None
        return href, brain


# Export the function for easy import
__all__ = ["resolve_uid"]
