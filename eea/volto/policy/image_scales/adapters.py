"""
EEA ImageScales adapters.

Provides image_scales catalog index support with field inheritance.
- Plone 5: Full implementation (ImageScales + ImageFieldScales)
- Plone 6: Extends plone.namedfile's ImageFieldScales, delegates inheritance
           to our ImageFieldScales
"""

from Acquisition import aq_inner
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.utils import iterSchemata
from plone.namedfile.interfaces import INamedImageField
from plone.registry.interfaces import IRegistry
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface.interfaces import ComponentLookupError
from zope.schema import getFields

from eea.volto.policy.inherit import (
    get_inheritable_fields,
    get_inherited_field_value,
)
from eea.volto.policy.image_scales.interfaces import (
    IImageScalesAdapter,
    IImageScalesFieldAdapter as IPlone5ImageScalesFieldAdapter,
    IImagingSchema,
)

# Plone 6 imports
try:
    from plone.namedfile.adapters import ImageFieldScales as PloneImageFieldScales
    from plone.base.interfaces import (
        IImageScalesFieldAdapter as IPlone6ImageScalesFieldAdapter,
    )

    HAS_PLONE6 = True
except ImportError:
    PloneImageFieldScales = object
    IPlone6ImageScalesFieldAdapter = Interface
    HAS_PLONE6 = False


# =============================================================================
# Plone 5: Full implementation
# =============================================================================


def _split_scale_info(allowed_size):
    """
    get desired attr(name,width,height) from scale names
    """
    name, dims = allowed_size.split(" ")
    width, height = list(map(int, dims.split(":")))
    return name, width, height


def _get_scale_infos():
    """Returns list of (name, width, height) of the available image scales."""
    if IImagingSchema is None:
        return []
    registry = getUtility(IRegistry)
    imaging_settings = registry.forInterface(
        IImagingSchema, prefix="plone", omit=("picture_variants")
    )
    allowed_sizes = imaging_settings.allowed_sizes
    return [_split_scale_info(size) for size in allowed_sizes]


@implementer(IImageScalesAdapter)
@adapter(IDexterityContent, Interface)
class ImageScales:
    """
    Adapter for getting image scales (Plone 5).
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        obj = aq_inner(self.context)
        res = {}
        for schema in iterSchemata(self.context):
            for name, field in getFields(schema).items():
                # serialize the field
                serializer = queryMultiAdapter(
                    (field, obj, self.request), IPlone5ImageScalesFieldAdapter
                )
                if serializer:
                    scales = serializer()
                    if scales:
                        res[name] = scales
        return res


@implementer(IPlone5ImageScalesFieldAdapter)
@adapter(INamedImageField, IDexterityContent, Interface)
class ImageFieldScales:
    """
    Image scale serializer with inheritance support.

    Used directly by Plone 5, and as fallback for Plone 6 when
    inheritance is needed.
    """

    def __init__(self, field, context, request):
        self.context = context
        self.request = request
        self.field = field

    def __call__(self):
        image = self.field.get(self.context)
        field_name = self.field.__name__
        source_obj = None

        # Check inheritance if no local image
        if not image and field_name in get_inheritable_fields():
            image, source_obj = get_inherited_field_value(
                self.context,
                field_name,
            )

        if not image:
            return None

        # Use source object for @@images view if inherited
        images_context = source_obj if source_obj else self.context

        try:
            self.images_view = getMultiAdapter(
                (images_context, self.request), name="images"
            )
        except ComponentLookupError:
            # Seen in plone.app.caching.tests.test_profile_with_caching_proxy.
            # If we cannot find the images view, there is nothing for us to do.
            return None

        self._images_context = images_context
        self._inherited = True if source_obj else False
        width, height = image.getImageSize()
        url = self.get_original_image_url(field_name, width, height)
        scales = self.get_scales(self.field, width, height)

        result = {
            "filename": image.filename,
            "content-type": image.contentType,
            "size": image.getSize(),
            "download": self._scale_view_from_url(url),
            "width": width,
            "height": height,
            "scales": scales,
        }

        if source_obj:
            result["inherited_from"] = {
                "@id": source_obj.absolute_url(),
                "title": source_obj.title,
            }

        return [result]

    def get_scales(self, field, width, height):
        """Get a dictionary of available scales for a particular image field,
        with the actual dimensions (aspect ratio of the original image).
        """
        scales = {}

        for name, actual_width, actual_height in _get_scale_infos():
            if actual_width > width:
                # The width of the scale is larger than the original width.
                # Scaling would simply return the original (or perhaps a copy
                # with the same size).  We do not need this scale.
                # If we *do* want this, we should call the scale method with
                # mode="cover", so it scales up.
                continue

                # Get the scale info without actually generating the scale,
                # nor any old-style HiDPI scales.
            scale = self.images_view.scale(
                field.__name__,
                width=actual_width,
                height=actual_height,
            )
            if scale is None:
                # If we cannot get a scale, it is probably a corrupt image.
                continue

            url = scale.url
            actual_width = scale.width
            actual_height = scale.height

            scales[name] = {
                "download": self._scale_view_from_url(url),
                "width": actual_width,
                "height": actual_height,
            }

        return scales

    def get_original_image_url(self, fieldname, width, height):
        """
        get image url from scale
        """
        scale = self.images_view.scale(
            fieldname,
            width=width,
            height=height,
        )
        # Corrupt images may not have a scale.
        return scale.url if scale else None

    def _scale_view_from_url(self, url):
        """Strip context URL to get relative scale path."""
        context = getattr(self, "_images_context", self.context)
        if self._inherited:
            return url
        return url.replace(context.absolute_url(), "").lstrip("/")


# =============================================================================
# Plone 6: Wrapper that delegates inheritance to ImageFieldScales
# =============================================================================

if HAS_PLONE6:

    @implementer(IPlone6ImageScalesFieldAdapter)
    @adapter(INamedImageField, IDexterityContent, Interface)
    class EEAImageFieldScales(PloneImageFieldScales):
        """
        Plone 6 image scale serializer with inheritance support.

        If local image exists, uses Plone's default implementation.
        If no local image, delegates to ImageFieldScales for inheritance.
        """

        def __call__(self):
            if self.field.get(self.context):
                return super().__call__()

            # Delegate to our inheritance-aware implementation
            return ImageFieldScales(self.field, self.context, self.request)()
