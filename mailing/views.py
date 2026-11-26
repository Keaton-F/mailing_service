from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import ClientForm, MailingForm, MessageForm
from .models import Client, Mailing, MailingAttempt, Message
from .services import send_mailing


def is_manager(user: Any) -> bool:
    """Проверяет, является ли пользователь менеджером или суперпользователем."""
    return bool(user.is_superuser or user.groups.filter(name="Менеджер").exists())


class OwnerFilterMixin(LoginRequiredMixin):
    """Фильтрует queryset: менеджеры видят всё, обычные пользователи — только свои объекты."""

    def get_queryset(self) -> QuerySet[Any]:
        qs: QuerySet[Any] = super().get_queryset()  # type: ignore[misc]
        if is_manager(self.request.user):  # type: ignore[attr-defined]
            return qs
        return qs.filter(owner=self.request.user)  # type: ignore[attr-defined]


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Разрешает редактирование и удаление только владельцу объекта."""

    def test_func(self) -> bool:
        obj = self.get_object()  # type: ignore[attr-defined]
        return bool(obj.owner == self.request.user)  # type: ignore[attr-defined]


class HomeView(TemplateView):
    """Главная страница со статистикой сервиса (с серверным кешированием в Redis)."""

    template_name = "mailing/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        now = timezone.now()

        stats = cache.get("home_global_stats")
        if stats is None:
            stats = {
                "total_mailings": Mailing.objects.count(),
                "active_mailings": Mailing.objects.filter(
                    status=Mailing.STATUS_STARTED,
                    start_time__lte=now,
                    end_time__gte=now,
                ).count(),
                "unique_clients": Client.objects.values("email").distinct().count(),
            }
            cache.set("home_global_stats", stats, 60 * 5)

        context.update(stats)

        if self.request.user.is_authenticated:
            user_attempts = MailingAttempt.objects.filter(mailing__owner=self.request.user)
            context["user_success_attempts"] = user_attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count()
            context["user_failed_attempts"] = user_attempts.filter(status=MailingAttempt.STATUS_FAILED).count()
            context["user_sent_messages"] = user_attempts.count()

        return context


# --- CRUD для получателей (Client) ---
class ClientListView(OwnerFilterMixin, ListView):
    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"


class ClientDetailView(OwnerFilterMixin, DetailView):
    model = Client
    template_name = "mailing/client_detail.html"
    context_object_name = "client"


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form: Any) -> HttpResponse:
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(OwnerRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(OwnerRequiredMixin, DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")


# --- CRUD для сообщений (Message) ---
class MessageListView(OwnerFilterMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"


class MessageDetailView(OwnerFilterMixin, DetailView):
    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message"


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form: Any) -> HttpResponse:
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(OwnerRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(OwnerRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


# --- CRUD для рассылок (Mailing), ручной запуск и отключение менеджером ---
class MailingListView(OwnerFilterMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"


class MailingDetailView(OwnerFilterMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def form_valid(self, form: Any) -> HttpResponse:
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(OwnerRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingDeleteView(OwnerRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingSendView(OwnerRequiredMixin, View):
    """Ручной запуск рассылки владельцем."""

    def get_object(self) -> Mailing:
        return get_object_or_404(Mailing, pk=self.kwargs["pk"])

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        mailing = self.get_object()
        success, result_message = send_mailing(mailing)
        if success:
            messages.success(request, result_message)
        else:
            messages.error(request, result_message)
        return redirect("mailing:mailing_detail", pk=pk)


class MailingDisableView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Отключение рассылки менеджером."""

    permission_required = "mailing.can_disable_mailing"

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = Mailing.STATUS_FINISHED
        mailing.end_time = timezone.now()
        mailing.save(update_fields=["status", "end_time"])
        messages.warning(request, f"Рассылка #{mailing.pk} отключена менеджером.")
        return redirect("mailing:mailing_detail", pk=pk)


class MailingAttemptListView(LoginRequiredMixin, ListView):
    """Просмотр истории попыток рассылок."""

    model = MailingAttempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"
    ordering = ["-attempt_time"]

    def get_queryset(self) -> QuerySet[MailingAttempt]:
        qs = super().get_queryset()
        if is_manager(self.request.user):
            return qs
        return qs.filter(mailing__owner=self.request.user)
