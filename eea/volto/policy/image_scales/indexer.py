# pylint: disable=ungrouped-imports
"""
Indexer
"""

from persistent.dict import PersistentDict
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer.decorator import indexer
from zope.component import queryMultiAdapter
from zope.globalrequest import getRequest
from zope.interface import Interface

try:
    from plone.base.interfaces import IImageScalesAdapter
except ImportError:
    # BBB Plone 5
    IImageScalesAdapter = Interface


@indexer(IDexterityContent)
def image_scales(obj):
    """
    Indexer used to store in metadata the image scales of the object.
    """
    adapter = queryMultiAdapter((obj, getRequest()), IImageScalesAdapter)
    if not adapter:
        # Raising an AttributeError does the right thing,
        # making sure nothing is saved in the catalog.
        raise AttributeError
    try:
        scales = adapter()
    except TypeError:
        scales = {}
    if not scales:
        raise AttributeError
    return PersistentDict(scales)
