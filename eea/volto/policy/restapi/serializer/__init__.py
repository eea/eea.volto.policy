"""RestAPI serializer

This module applies monkey patches to plone.restapi.serializer.blocks
"""

# Import monkey patches for plone.restapi.serializer.blocks
# This will apply the TeaserBlockSerializerBase._process_data patch
from .blocks import apply_teaser_block_monkey_patch

apply_teaser_block_monkey_patch()
