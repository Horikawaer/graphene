import binascii

from django.core.exceptions import ValidationError
from django.forms import CharField, Field, IntegerField, MultipleChoiceField
from django.utils.translation import ugettext_lazy as _
from graphql_relay import from_global_id


class GlobalIDFormField(Field):
    default_error_messages = {
        'invalid': _('Invalid ID specified.'),
    }

    def clean(self, value):
        if not value and not self.required:
            return None

        try:
            gid = from_global_id(value)
        except (TypeError, ValueError, UnicodeDecodeError, binascii.Error):
            raise ValidationError(self.error_messages['invalid'])

        try:
            IntegerField().clean(gid.id)
            CharField().clean(gid.type)
        except ValidationError:
            raise ValidationError(self.error_messages['invalid'])

        return value


class GlobalIDMultipleChoiceField(MultipleChoiceField):
    default_error_messages = {
        'invalid_choice': _('One of the specified IDs was invalid (%(value)s).'),
        'invalid_list': _('Enter a list of values.'),
    }

    def valid_value(self, value):
        # Clean will raise a validation error if there is a problem
        GlobalIDFormField().clean(value)
        return True
