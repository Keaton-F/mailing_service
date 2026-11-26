import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


def send_mailing(mailing: Mailing) -> None:
    """Отправляет рассылку всем привязанным получателям и фиксирует попытку."""
    now = timezone.now()

    # Если время рассылки еще не наступило или уже прошло, при ручном запуске обновляем статус
    if mailing.end_time < now:
        mailing.status = Mailing.STATUS_FINISHED
        mailing.save(update_fields=["status"])
        return

    mailing.status = Mailing.STATUS_STARTED
    mailing.save(update_fields=["status"])

    recipient_emails = list(mailing.clients.values_list("email", flat=True))

    if not recipient_emails:
        MailingAttempt.objects.create(
            status=MailingAttempt.STATUS_FAILED,
            server_response="Нет получателей для отправки рассылки.",
            mailing=mailing,
        )
        return

    try:
        sent_count = send_mail(
            subject=mailing.message.subject,
            message=mailing.message.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )
        MailingAttempt.objects.create(
            status=MailingAttempt.STATUS_SUCCESS,
            server_response=f"Письма успешно отправлены ({sent_count} шт.).",
            mailing=mailing,
        )
    except (smtplib.SMTPException, Exception) as exc:
        MailingAttempt.objects.create(
            status=MailingAttempt.STATUS_FAILED,
            server_response=str(exc),
            mailing=mailing,
        )
