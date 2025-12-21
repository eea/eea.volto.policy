from plone.dexterity.interfaces import IDexterityContent
from plone.indexer.decorator import indexer
from zope.interface import Interface

from eea.volto.policy.inherit import indexer_with_inheritance

try:
    from plone.volto.indexers.indexers import (
        image_field_indexer as plone_image_field_indexer,
        hasPreviewImage as ploneHasPreviewImage,
    )
    from plone.volto.behaviors.preview import IPreview
except ImportError:
    plone_image_field_indexer = None
    ploneHasPreviewImage = None
    IPreview = Interface


@indexer(IPreview)
def hasPreviewImage(obj):
    """
    Indexer for knowing in a catalog search if a content with the IPreview
    behavior has a preview_image
    """
    return indexer_with_inheritance(ploneHasPreviewImage, obj, ["preview_image"])


@indexer(IDexterityContent)
def image_field_indexer(obj):
    """Indexer for knowing in a catalog search if a content has any image."""
    return indexer_with_inheritance(
        plone_image_field_indexer, obj, ["preview_image_link", "preview_image", "image"]
    )
