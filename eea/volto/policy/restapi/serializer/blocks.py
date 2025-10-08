"""
eea.volto.policy.restapi.serializer.blocks overrides
"""

from plone.restapi.serializer.blocks import (
    TeaserBlockSerializerBase,
    url_to_brain,
)

from plone.restapi.interfaces import ISerializeToJsonSummary
from zope.component import getMultiAdapter


def patched_process_data(self, data, field=None):
    """Override _process_data to remove the href clearing logic for non-http"""
    print("Patched TeaserBlockSerializerBase._process_data called")
    value = data.get("href", "")
    if value:
        if isinstance(value, str):
            url = value
            value = [{"@id": url}]
        else:
            url = value[0].get("@id", "")
        brain = url_to_brain(url)
        if brain is not None:
            serialized_brain = getMultiAdapter(
                (brain, self.request), ISerializeToJsonSummary
            )()

            if not data.get("overwrite"):
                # Update fields at the top level of the block data
                for key in ["title", "description", "head_title"]:
                    if key in serialized_brain:
                        data[key] = serialized_brain[key]

            # We return the serialized brain.
            value[0].update(serialized_brain)
            data["href"] = value
        # NOTE: Removed the elif clause that clears href for non-http URLs
        # Original code was:
        # elif not url.startswith("http"):
        #     # Source not found; clear out derived fields
        #     data["href"] = []
    return data


def apply_teaser_block_monkey_patch():
    """Apply monkey patch to TeaserBlockSerializerBase._process_data"""
    TeaserBlockSerializerBase._process_data = patched_process_data
    print("EEA: Applied TeaserBlockSerializerBase monkey patch")
