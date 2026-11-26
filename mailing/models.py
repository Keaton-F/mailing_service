from django.conf import settings
from django.db import models


class Client(models.Model):
    """Модель «Получатель рассылки»"""

    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=255, verbose_name="Ф. И. О.")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "получатель рассылки"
        verbose_name_plural = "получатели рассылки"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    """Модель «Сообщение»"""

    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "сообщение"
        verbose_name_plural = "сообщения"

    def __str__(self) -> str:
        return str(self.subject)


class Mailing(models.Model):
    """Модель «Рассылка»"""

    STATUS_CREATED = "Создана"
    STATUS_STARTED = "Запущена"
    STATUS_FINISHED = "Завершена"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_STARTED, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время первой отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        verbose_name="Сообщение",
    )
    clients = models.ManyToManyField(
        Client,
        verbose_name="Получатели",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name="Владелец",
    )

    class Meta:
        verbose_name = "рассылка"
        verbose_name_plural = "рассылки"
        permissions = [
            ("can_disable_mailing", "Может отключать рассылки"),
        ]

    def __str__(self) -> str:
        return f"Рассылка #{self.pk} ({self.status})"


class MailingAttempt(models.Model):
    """Модель «Попытка рассылки»"""

    STATUS_SUCCESS = "Успешно"
    STATUS_FAILED = "Не успешно"

    STATUS_CHOICES = [
        (STATUS_SUCCESS, "Успешно"),
        (STATUS_FAILED, "Не успешно"),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время попытки")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name="Статус",
    )
    server_response = models.TextField(verbose_name="Ответ почтового сервера")
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    class Meta:
        verbose_name = "попытка рассылки"
        verbose_name_plural = "попытки рассылок"

    def __str__(self) -> str:
        return f"Попытка #{self.pk} для рассылки #{self.mailing_id} — {self.status}"
