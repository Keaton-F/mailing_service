from typing import Any

from django import forms

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
        fields = ("start_time", "end_time", "message", "clients")
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
