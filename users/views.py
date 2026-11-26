import secrets
from typing import Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView

from .forms import UserLoginForm, UserPasswordResetForm, UserRegisterForm, UserSetPasswordForm
from .models import User


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form: Any) -> HttpResponse:
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()

        host = self.request.get_host()
        url = f"http://{host}{reverse('users:email_confirm', kwargs={'token': token})}"

        send_mail(
            subject="Confirm registration on MailingService",
            message=f"Hello! To confirm your email, please follow the link:\n{url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        messages.info(
            self.request, "Ссылка для подтверждения регистрации отправлена на ваш Email (проверьте консоль)."
        )
        return super().form_valid(form)


def email_verification(request: HttpRequest, token: str) -> HttpResponse:
    """Активация аккаунта при переходе по ссылке из письма."""
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.token = None
    user.save()
    messages.success(request, "Почта успешно подтверждена! Теперь вы можете войти.")
    return redirect("users:login")


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"


class UserLogoutView(LogoutView):
    pass


class UserPasswordResetView(PasswordResetView):
    form_class = UserPasswordResetForm
    template_name = "users/password_reset_form.html"
    email_template_name = "users/password_reset_email.html"
    success_url = reverse_lazy("users:password_reset_done")


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = "users/password_reset_done.html"


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = UserSetPasswordForm
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:password_reset_complete")


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "users/password_reset_complete.html"


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Проверка, что пользователь состоит в группе Менеджер или является суперпользователем."""

    def test_func(self) -> bool:
        user = self.request.user  # type: ignore[attr-defined]
        return bool(user.is_superuser or user.groups.filter(name="Менеджер").exists())


class UserListView(ManagerRequiredMixin, ListView):
    """Просмотр списка пользователей сервиса (только для менеджеров)."""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"


class ToggleUserActiveView(ManagerRequiredMixin, View):
    """Блокировка или разблокировка пользователя сервиса (только для менеджеров)."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        target_user = get_object_or_404(User, pk=pk)
        if not target_user.is_superuser:
            target_user.is_active = not target_user.is_active
            target_user.save(update_fields=["is_active"])
            status_text = "разблокирован" if target_user.is_active else "заблокирован"
            messages.success(request, f"Пользователь {target_user.email} {status_text}.")
        return redirect("users:user_list")
