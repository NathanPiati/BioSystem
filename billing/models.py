from django.db import models
from django.utils import timezone

from personais.models import PersonalTrainer


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Ativa'),
        ('OVERDUE', 'Vencida'),
        ('CANCELED', 'Cancelada'),
        ('EXPIRED', 'Expirada'),
        ('PENDING', 'Pendente'),
    ]

    personal = models.OneToOneField(
        PersonalTrainer,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Personal',
    )
    asaas_customer_id = models.CharField(max_length=100, unique=True)
    asaas_subscription_id = models.CharField(
        max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING')
    next_due_date = models.DateField(null=True, blank=True)
    payment_url = models.URLField(blank=True)
    access_until = models.DateTimeField(null=True, blank=True)
    last_event_key = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_access(self):
        return self.status == 'ACTIVE' and (
            self.access_until is None or self.access_until >= timezone.now()
        )

    def __str__(self):
        return f'{self.personal} - {self.get_status_display()}'


class AsaasWebhookEvent(models.Model):
    event_key = models.CharField(max_length=200, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.event_type} - {self.event_key}'
