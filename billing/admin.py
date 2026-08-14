from django.contrib import admin

from .models import AsaasWebhookEvent, Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('personal', 'status', 'next_due_date', 'access_until')
    list_filter = ('status',)
    search_fields = ('personal__email', 'asaas_customer_id',
                     'asaas_subscription_id')


@admin.register(AsaasWebhookEvent)
class AsaasWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_key', 'event_type', 'received_at')
    list_filter = ('event_type',)
    readonly_fields = ('event_key', 'event_type', 'payload', 'received_at')
