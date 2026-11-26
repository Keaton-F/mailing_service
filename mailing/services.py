import smtplib

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Mailing, MailingAttempt


def send_mailing(mailing: Mailing) -> tuple[bool, str]:
    """Проверяет временное окно, отправляет письма каждому получателю и сохраняет попытки через bulk_create."""
    now = timezone.now()

    if not (mailing.start_time <= now <= mailing.end_time):
        if now < mailing.start_time:
            mailing.status = Mailing.STATUS_CREATED
            mailing.save(update_fields=["status"])
            return False, "Время начала рассылки еще не наступило."
        mailing.status = Mailing.STATUS_FINISHED
        mailing.save(update_fields=["status"])
        return False, "Время окончания рассылки уже прошло."

    mailing.status = Mailing.STATUS_STARTED
    mailing.save(update_fields=["status"])

    recipients = list(mailing.recipients.all())
    if not recipients:
        return False, "В рассылке не выбрано ни одного получателя."

    attempts: list[MailingAttempt] = []
    for client in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            attempts.append(
                MailingAttempt(
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response=f"Письмо для {client.email} успешно отправлено.",
                    mailing=mailing,
                )
            )
        except (smtplib.SMTPException, Exception) as exc:
            attempts.append(
                MailingAttempt(
                    status=MailingAttempt.STATUS_FAILED,
                    server_response=f"Ошибка отправки для {client.email}: {exc}",
                    mailing=mailing,
                )
            )

    MailingAttempt.objects.bulk_create(attempts)
    return True, f"Рассылка выполнена. Обработано получателей: {len(attempts)}."
