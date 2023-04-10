""" DXFields
"""
import dateutil
import pytz
from eea.volto.policy.interfaces import IEeaVoltoPolicyLayer
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.app.event.base import default_timezone
from plone.dexterity.interfaces import IDexterityContent
from plone.restapi.deserializer.dxfields import \
    DatetimeFieldDeserializer as DefaultDatetimeFieldDeserializer
from plone.restapi.interfaces import IFieldDeserializer
from pytz import timezone, utc
from z3c.form.interfaces import IDataManager
from zope.component import adapter, queryMultiAdapter
from zope.interface import implementer
from zope.schema.interfaces import IDatetime


@implementer(IFieldDeserializer)
@adapter(IDatetime, IDexterityContent, IEeaVoltoPolicyLayer)
class DatetimeFieldDeserializer(DefaultDatetimeFieldDeserializer):
    """ DatetimeFieldDeserializer
    """
    def __call__(self, value):
        # PATCH
        is_publication_field = self.field.interface == IPublication
        if is_publication_field:
            # because IPublication datamanager strips timezones
            tzinfo = pytz.timezone(default_timezone())
        else:
            dm = queryMultiAdapter((self.context, self.field), IDataManager)
            current = dm.get()
            if current is not None:
                tzinfo = current.tzinfo
            else:
                tzinfo = None
        # END OF PATCH

        # This happens when a 'null' is posted for a non-required field.
        if value is None:
            self.field.validate(value)
            return

        # Parse ISO 8601 string with dateutil
        try:
            dt = dateutil.parser.parse(value)
        except ValueError as err:
            raise ValueError(f"Invalid date {err}: {value}") from err

        # Convert to TZ aware in UTC
        if dt.tzinfo is not None:
            dt = dt.astimezone(utc)
        else:
            dt = utc.localize(dt)

        # Convert to local TZ aware or naive UTC
        if tzinfo is not None:
            tz = timezone(tzinfo.zone)
            value = tz.normalize(dt.astimezone(tz))
        else:
            value = utc.normalize(dt.astimezone(utc)).replace(tzinfo=None)

        # if it's an IPublication field, remove timezone info to not break field validation
        # PATCH
        if is_publication_field:
            value = value.replace(tzinfo=None)
        # END OF PATCH
        self.field.validate(value)
        return value
