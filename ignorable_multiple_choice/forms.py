from django.core.exceptions import ValidationError
from django.forms import ModelMultipleChoiceField as _ModelMultipleChoiceField
from django.forms import MultipleChoiceField as _MultipleChoiceField
from django.forms import TypedMultipleChoiceField as _TypedMultipleChoiceField

__all__ = [
    "MultipleChoiceField",
    "TypedMultipleChoiceField",
    "ModelMultipleChoiceField",
]


class MultipleChoiceField(_MultipleChoiceField):

    def __init__(self, *, ignore_invalid_choice=False, **kwargs):
        self.ignore_invalid_choice = ignore_invalid_choice
        super().__init__(**kwargs)

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages["required"],
                code="required",
            )

    def clean(self, value):
        value = self.to_python(value)
        if self.ignore_invalid_choice:
            value = [val for val in value if self.valid_value(val)]
        else:
            # Validate that each value in the value list is in self.choices.
            for val in value:
                if not self.valid_value(val):
                    raise ValidationError(
                        self.error_messages["invalid_choice"],
                        code="invalid_choice",
                        params={"value": val},
                    )
        self.validate(value)
        self.run_validators(value)
        return value


class TypedMultipleChoiceField(_TypedMultipleChoiceField):

    def __init__(self, *, ignore_invalid_choice=False, **kwargs):
        self.ignore_invalid_choice = ignore_invalid_choice
        super().__init__(**kwargs)

    def validate(self, value):
        if value != self.empty_value:
            if self.required and not value:
                raise ValidationError(
                    self.error_messages["required"],
                    code="required",
                )
        elif self.required:
            raise ValidationError(
                self.error_messages["required"],
                code="required",
            )

    def clean(self, value):
        value = self.to_python(value)
        if self.ignore_invalid_choice:
            value = [val for val in value if self.valid_value(val)]
        else:
            # Validate that each value in the value list is in self.choices.
            for val in value:
                if not self.valid_value(val):
                    raise ValidationError(
                        self.error_messages["invalid_choice"],
                        code="invalid_choice",
                        params={"value": val},
                    )
        self.validate(value)
        self.run_validators(value)
        return self._coerce(value)


class ModelMultipleChoiceField(_ModelMultipleChoiceField):

    def __init__(self, *args, ignore_invalid_choice=False, **kwargs):
        self.ignore_invalid_choice = ignore_invalid_choice
        super().__init__(*args, **kwargs)

    def _check_values(self, value):
        """
        Given a list of possible PK values, return a QuerySet of the
        corresponding objects. Raise a ValidationError if a given value is
        invalid (not a valid PK, not in the queryset, etc.)
        """
        key = self.to_field_name or "pk"
        # deduplicate given values to avoid creating many querysets or
        # requiring the database backend deduplicate efficiently.
        try:
            value = frozenset(value)
        except TypeError:
            # list of lists isn't hashable, for example
            raise ValidationError(
                self.error_messages["invalid_list"],
                code="invalid_list",
            )
        for pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except (ValueError, TypeError):
                raise ValidationError(
                    self.error_messages["invalid_pk_value"],
                    code="invalid_pk_value",
                    params={"pk": pk},
                )
        qs = self.queryset.filter(**{"%s__in" % key: value})
        if not self.ignore_invalid_choice:
            pks = {str(getattr(o, key)) for o in qs}
            for val in value:
                if str(val) not in pks:
                    raise ValidationError(
                        self.error_messages["invalid_choice"],
                        code="invalid_choice",
                        params={"value": val},
                    )
        return qs
