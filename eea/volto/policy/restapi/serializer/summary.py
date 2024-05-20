"""Summary serializer metadata for EEA Volto Policy."""
from plone.restapi.interfaces import IJSONSummarySerializerMetadata
from plone.restapi.serializer.summary import JSONSummarySerializerMetadata
from zope.interface import implementer


@implementer(IJSONSummarySerializerMetadata)
class EEAJSONSummarySerializerMetadata(JSONSummarySerializerMetadata):
    """
    Summary Metadata serializer inherited within EEA Volto Policy.

    Implements IJSONSummarySerializerMetadata interface.
    """

    def default_metadata_fields(self):
        """
        Returns a set of default metadata fields to be included in the summary.
        We add effective date to the list of default fields.
        Returns:
            set: A set of metadata field names.
        """
        return {
            "@id",
            "@type",
            "description",
            "review_state",
            "title",
            "type_title",
            "effective",
        }
