from typing import Any

from django.core.management import BaseCommand
from django.utils import timezone

from mailing.models import Mailing
from mailing.services import send_mailing


class Command(BaseCommand):
    help = "Запускает отправку всех активных и готовых к запуску рассылок."

    def handle(self, *args: Any, **options: Any) -> None:
        now = timezone.now()
        mailings = Mailing.objects.filter(
            status__in=[Mailing.STATUS_CREATED, Mailing.STATUS_STARTED],
            start_time__lte=now,
            end_time__gte=now,
        )

        if not mailings.exists():
            self.stdout.write(self.style.WARNING("Нет активных рассылок для отправки."))
            return

        for mailing in mailings:
            send_mailing(mailing)
            self.stdout.write(self.style.SUCCESS(f"Рассылка #{mailing.pk} обработана."))
