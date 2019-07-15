from marshmallow import Schema, fields

from jwallet_updates.validate import SemverField


class IOSConfigSchema(Schema):
    minimal_actual_version = SemverField(required=True)
    force_update = fields.List(SemverField(), required=True)
    latest_version = SemverField(required=True)
    force_off = fields.List(SemverField(), required=True)


class AndroidConfigSchema(Schema):
    minimal_actual_version = SemverField(required=True)
    force_update = fields.List(SemverField(), required=True)
