"""Expose EEA-specific fields through the Subsite expansion."""

from collective.volto.subsites.content.subsite import ISubsite
from collective.volto.subsites.restapi.services.subsite.get import (
    Subsite as BaseSubsite,
)
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.serializer.converters import json_compatible
from zope.component import queryMultiAdapter

from eea.volto.policy.behaviors.subsite import ISubsiteLogoMain


class Subsite(BaseSubsite):
    """Add EEA behavior fields to the existing Subsite expansion."""

    def get_subsite_info(self):
        data = super().get_subsite_info()
        if not data:
            return data

        subsite = next(
            (item for item in self.context.aq_chain if ISubsite.providedBy(item)),
            None,
        )
        if subsite is None or not ISubsiteLogoMain.providedBy(subsite):
            return data

        name = "subsite_logo_main"
        field = ISubsiteLogoMain[name]
        serializer = queryMultiAdapter((field, subsite, self.request), IFieldSerializer)
        data[json_compatible(name)] = serializer()
        return data
