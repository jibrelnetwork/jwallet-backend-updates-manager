from marshmallow import  ValidationError
from marshmallow.fields import ValidatedField, String as fString, Validator
import semver


class SemverValidator(Validator):
    """Validate a semver value.

    :param str error: Error message to raise in case of a validation error. Can be
        interpolated with `{input}`.
    """

    default_message = 'Not a valid semver value.'

    def __init__(self, error=None):
        self.error = error or self.default_message

    def _format_error(self, value):
        return self.error.format(input=value)

    def __call__(self, value):
        message = self._format_error(value)

        try:
            version = semver.VersionInfo.parse(value)
        except ValueError as e:
           raise ValidationError(message)

        return value


class SemverField(ValidatedField, fString):
    """A validated semver field. Validation occurs during both serialization and
    deserialization.

    :param args: The same positional arguments that :class:`String` receives.
    :param kwargs: The same keyword arguments that :class:`String` receives.
    """
    default_error_messages = {'invalid': 'Not a valid semver value.'}

    def __init__(self, *args, **kwargs):
        fString.__init__(self, *args, **kwargs)
        self.validators.insert(0, SemverValidator(error=self.error_messages['invalid']))

    def _validated(self, value):
        if value is None:
            return None
        return SemverValidator(
            error=self.error_messages['invalid']
        )(value)
