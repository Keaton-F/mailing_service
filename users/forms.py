from typing import Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm

from .models import User


class StyleFormMixin:
    """Миксин для автоматической стилизации полей формы под Bootstrap."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():  # type: ignore[attr-defined]
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})


class UserRegisterForm(StyleFormMixin, UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "avatar", "phone_number", "country")


class UserLoginForm(StyleFormMixin, AuthenticationForm):
    pass


class UserPasswordResetForm(StyleFormMixin, PasswordResetForm):
    pass


class UserSetPasswordForm(StyleFormMixin, SetPasswordForm):
    pass
