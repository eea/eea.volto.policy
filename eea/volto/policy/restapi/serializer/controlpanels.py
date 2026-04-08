"""Custom serializer for the unified EEA Settings controlpanel."""

from plone.dexterity.interfaces import IDexterityContent
from plone.registry.interfaces import IRegistry
from plone.restapi.interfaces import IFieldSerializer
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.controlpanels import (
    get_jsonschema_for_controlpanel,
)
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import noLongerProvides

from eea.volto.policy.interfaces import IEEASettingsControlpanel

import zope.schema


SERVICE_ID = "@controlpanels"


class _ProviderProxy:
    """Minimal proxy that makes the controlpanel serializer helper work
    with an arbitrary provider schema."""

    def __init__(self, panel, provider_schema, provider_prefix):
        self.context = panel.context
        self.request = panel.request
        self.schema = provider_schema
        self.schema_prefix = provider_prefix


@implementer(ISerializeToJson)
@adapter(IEEASettingsControlpanel)
class EEASettingsControlpanelSerializer:
    """Serializes the unified controlpanel by aggregating all providers."""

    def __init__(self, controlpanel):
        self.controlpanel = controlpanel
        self.registry = getUtility(IRegistry)

    def __call__(self):
        result = {
            "@id": "{}/{}/{}".format(
                self.controlpanel.context.absolute_url(),
                SERVICE_ID,
                self.controlpanel.__name__,
            ),
            "title": self.controlpanel.title,
            "group": self.controlpanel.group,
            "schema": {
                "type": "object",
                "properties": {},
                "required": [],
                "fieldsets": [],
            },
            "data": {},
        }

        for name, provider in self.controlpanel.get_providers():
            provider_schema = getattr(provider, "schema", None)
            if provider_schema is None:
                continue

            provider_prefix = getattr(provider, "schema_prefix", None)
            provider_title = getattr(provider, "title", name)

            # Build JSON schema for this provider
            proxy = _ProviderProxy(
                self.controlpanel, provider_schema, provider_prefix
            )
            json_schema = get_jsonschema_for_controlpanel(
                proxy,
                self.controlpanel.context,
                self.controlpanel.request,
            )

            # Merge properties
            result["schema"]["properties"].update(
                json_schema.get("properties", {})
            )
            result["schema"]["required"].extend(
                json_schema.get("required", [])
            )

            # Create a fieldset per provider
            field_names = list(json_schema.get("properties", {}).keys())
            result["schema"]["fieldsets"].append(
                {
                    "id": name,
                    "title": provider_title,
                    "fields": field_names,
                }
            )

            # Serialize data from registry
            try:
                registry_proxy = self.registry.forInterface(
                    provider_schema, prefix=provider_prefix
                )
            except KeyError:
                continue

            alsoProvides(registry_proxy, IDexterityContent)
            for field_name, field in zope.schema.getFields(
                provider_schema
            ).items():
                serializer = queryMultiAdapter(
                    (field, registry_proxy, self.controlpanel.request),
                    IFieldSerializer,
                )
                if serializer:
                    value = serializer()
                else:
                    value = getattr(registry_proxy, field_name, None)
                result["data"][field_name] = value
            noLongerProvides(registry_proxy, IDexterityContent)

        return result
