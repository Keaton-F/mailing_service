from django.contrib import admin

from .models import Client, Mailing, MailingAttempt, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "full_name", "owner")
    search_fields = ("email", "full_name")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "owner")
    search_fields = ("subject",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time", "status", "message", "owner")
    list_filter = ("status",)


@admin.register(MailingAttempt)
class MailingAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt_time", "status", "mailing")
    list_filter = ("status",)
