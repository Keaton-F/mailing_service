from typing import Any

from django.contrib.auth.models import Group, Permission
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Создает группу 'Менеджер' и назначает ей необходимые права просмотра и отключения рассылок."

    def handle(self, *args: Any, **options: Any) -> None:
        group, _ = Group.objects.get_or_create(name="Менеджер")

        # Права на просмотр клиентов, сообщений, рассылок, пользователей и отключение рассылок
        codenames = [
            "view_client",
            "view_message",
            "view_mailing",
            "can_disable_mailing",
            "view_user",
        ]
        permissions = Permission.objects.filter(codename__in=codenames)
        group.permissions.set(permissions)

        self.stdout.write(self.style.SUCCESS("Группа 'Менеджер' успешно создана и настроена."))
