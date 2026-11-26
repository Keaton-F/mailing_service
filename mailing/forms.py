from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Client, Mailing, Message


class StyleFormMixin:
    """Миксин для автоматической стилизации полей формы под Bootstrap."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():  # type: ignore[attr-defined]
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-check-input"})
            elif isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})


class ClientForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = ("email", "full_name", "comment")


class MessageForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Message
        fields = ("subject", "body")


class MailingForm(StyleFormMixin, forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ("start_time", "end_time", "message", "recipients")
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def clean(self) -> dict[str, Any]:
        cleaned_data = cast(dict[str, Any], super().clean())
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and not self.instance.pk and start_time < timezone.now():
            raise ValidationError("Дата и время начала отправки не могут быть в прошлом.")

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("Дата и время начала отправки должны быть раньше времени окончания.")

        return cleaned_data
