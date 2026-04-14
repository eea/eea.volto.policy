"""Custom deserializer for the unified EEA Settings controlpanel."""

from plone.registry.interfaces import IRegistry
from plone.restapi.deserializer import json_body
from plone.restapi.interfaces import IDeserializeFromJson
from z3c.form.interfaces import IManagerValidator
from zExceptions import BadRequest
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.i18n import translate
from zope.interface import implementer
from zope.schema import getFields
from zope.schema.interfaces import ValidationError
from zope.interface.exceptions import Invalid

from eea.volto.policy.interfaces import IEEASettingsControlpanel


@implementer(IDeserializeFromJson)
@adapter(IEEASettingsControlpanel)
class EEASettingsControlpanelDeserializer:
    """Deserializes PATCH data by routing fields to the correct provider."""

    def __init__(self, controlpanel):
        self.controlpanel = controlpanel
        self.registry = getUtility(IRegistry)
        self.context = controlpanel.context
        self.request = controlpanel.request

    def __call__(self, mask_validation_errors=True):
        data = json_body(self.request)
        errors = []
        schema_data = {}

        for name, provider in self.controlpanel.get_providers():
            provider_schema = getattr(provider, "schema", None)
            if provider_schema is None:
                continue

            provider_prefix = getattr(provider, "schema_prefix", None)

            try:
                proxy = self.registry.forInterface(
                    provider_schema, prefix=provider_prefix
                )
            except KeyError:
                continue

            for field_name, field in getFields(provider_schema).items():
                full_field_name = f"{name}.{field_name}"
                if field.readonly or full_field_name not in data:
                    continue

                field_data = schema_data.setdefault(provider_schema, {})

                try:
                    value = data[full_field_name]
                    field.validate(value)
                    setattr(proxy, field_name, value)
                except ValidationError as e:
                    errors.append(
                        {
                            "message": e.doc(),
                            "field": full_field_name,
                            "error": e,
                        }
                    )
                except (ValueError, Invalid) as e:
                    errors.append(
                        {
                            "message": str(e),
                            "field": full_field_name,
                            "error": e,
                        }
                    )
                else:
                    field_data[field_name] = value

        # Validate schemata
        for schema, field_data in schema_data.items():
            validator = queryMultiAdapter(
                (self.context, self.request, None, schema, None),
                IManagerValidator,
            )
            if validator:
                for error in validator.validate(field_data):
                    errors.append({"error": error, "message": str(error)})

        if errors:
            for error in errors:
                if mask_validation_errors:
                    error["error"] = "ValidationError"
                error["message"] = translate(error["message"], context=self.request)
            raise BadRequest(errors)

        return True
