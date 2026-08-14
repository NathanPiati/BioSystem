from django.urls import path

from .views import asaas_webhook, subscription_checkout


urlpatterns = [
    path('assinatura/', subscription_checkout, name='subscription_checkout'),
    path('webhooks/asaas/', asaas_webhook, name='asaas_webhook'),
    path('assinatura/webhook/asaas/', asaas_webhook,
         name='asaas_subscription_webhook'),
]
