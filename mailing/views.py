from typing import Any

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import ClientForm, MailingForm, MessageForm
from .models import Client, Mailing, MailingAttempt, Message
from .services import send_mailing


class HomeView(TemplateView):
    """Главная страница со статистикой сервиса."""

    template_name = "mailing/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context: dict[str, Any] = super().get_context_data(**kwargs)
        context["total_mailings"] = Mailing.objects.count()
        context["active_mailings"] = Mailing.objects.filter(status=Mailing.STATUS_STARTED).count()
        context["unique_clients"] = Client.objects.values("email").distinct().count()
        return context


# --- CRUD для получателей (Client) ---
class ClientListView(ListView):
    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"


class ClientDetailView(DetailView):
    model = Client
    template_name = "mailing/client_detail.html"
    context_object_name = "client"


class ClientCreateView(CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")


class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")


# --- CRUD для сообщений (Message) ---
class MessageListView(ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"


class MessageDetailView(DetailView):
    model = Message
    template_name = "mailing/message_detail.html"
    context_object_name = "message"


class MessageCreateView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageUpdateView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


# --- CRUD для рассылок (Mailing) и ручной запуск ---
class MailingListView(ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"


class MailingDetailView(DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"
    context_object_name = "mailing"


class MailingCreateView(CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingUpdateView(UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingDeleteView(DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingSendView(View):
    """Ручной запуск рассылки по требованию из интерфейса."""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        mailing = get_object_or_404(Mailing, pk=pk)
        send_mailing(mailing)
        return redirect("mailing:mailing_detail", pk=pk)


class MailingAttemptListView(ListView):
    """Просмотр истории попыток рассылок."""

    model = MailingAttempt
    template_name = "mailing/attempt_list.html"
    context_object_name = "attempts"
    ordering = ["-attempt_time"]
