import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
import requests

from .models import AsaasWebhookEvent, Subscription


def _get_personal(user):
    try:
        return user.personaltrainer
    except AttributeError:
        return None


def _asaas_headers():
    return {
        'access_token': settings.ASAAS_API_KEY,
        'Content-Type': 'application/json',
        'User-Agent': 'Evolutty/1.0',
    }


def _asaas_url(path):
    return f'{settings.ASAAS_API_URL.rstrip("/")}/{path.lstrip("/")}'


def _asaas_error(response):
    try:
        errors = response.json().get('errors', [])
        if errors:
            return '; '.join(error.get('description', 'Erro da API') for error in errors)
    except ValueError:
        pass
    return f'Asaas retornou HTTP {response.status_code}.'


@login_required(login_url='login')
def subscription_checkout(request):
    personal = _get_personal(request.user)
    if not personal:
        return redirect('portal_home')
    if personal.subscription_exempt:
        return redirect('portal_home')

    subscription = Subscription.objects.filter(personal=personal).first()
    if request.method == 'POST':
        if subscription and subscription.payment_url and subscription.status == 'PENDING':
            return redirect(subscription.payment_url)

        try:
            monthly_value = Decimal(str(settings.ASAAS_MONTHLY_VALUE))
        except (InvalidOperation, TypeError):
            monthly_value = Decimal('0')

        if monthly_value <= 0 or not settings.ASAAS_API_KEY:
            messages.error(
                request, 'A cobrança ainda não foi configurada pelo administrador.')
        else:
            try:
                customer_id = subscription.asaas_customer_id if subscription else None
                if not customer_id:
                    response = requests.post(
                        _asaas_url('customers'),
                        headers=_asaas_headers(),
                        json={
                            'name': f'{personal.first_name} {personal.last_name}'.strip(),
                            'email': personal.email,
                            'cpfCnpj': personal.cpf,
                            'notificationDisabled': False,
                        },
                        timeout=15,
                    )
                    response.raise_for_status()
                    customer_id = response.json()['id']

                due_date = date.today() + timedelta(days=1)
                response = requests.post(
                    _asaas_url('subscriptions'),
                    headers=_asaas_headers(),
                    json={
                        'customer': customer_id,
                        'billingType': settings.ASAAS_BILLING_TYPE,
                        'value': float(monthly_value),
                        'cycle': 'MONTHLY',
                        'nextDueDate': due_date.isoformat(),
                        'description': settings.ASAAS_SUBSCRIPTION_DESCRIPTION,
                    },
                    timeout=15,
                )
                if not response.ok:
                    messages.error(request, _asaas_error(response))
                    return render(request, 'billing/subscription.html', {
                        'title': 'Assinatura Evolutty',
                        'subscription': subscription,
                        'monthly_value': settings.ASAAS_MONTHLY_VALUE,
                    })
                asaas_subscription = response.json()
                subscription, _ = Subscription.objects.update_or_create(
                    personal=personal,
                    defaults={
                        'asaas_customer_id': customer_id,
                        'asaas_subscription_id': asaas_subscription['id'],
                        'status': 'PENDING',
                        'next_due_date': asaas_subscription.get('nextDueDate'),
                    },
                )

                payments_response = requests.get(
                    _asaas_url(
                        f"subscriptions/{asaas_subscription['id']}/payments"),
                    headers=_asaas_headers(),
                    timeout=15,
                )
                payments_response.raise_for_status()
                payments = payments_response.json().get('data', [])
                payment_url = next(
                    (payment.get('invoiceUrl') or payment.get('bankSlipUrl') or payment.get('paymentLink')
                     for payment in payments if payment.get('status') in ('PENDING', 'OVERDUE')),
                    None,
                )
                if payment_url:
                    subscription.payment_url = payment_url
                    subscription.save(
                        update_fields=['payment_url', 'updated_at'])
                    return redirect(payment_url)

                messages.success(
                    request, 'Assinatura criada. A cobrança ficará disponível em instantes.')
            except (requests.RequestException, KeyError, ValueError) as error:
                messages.error(
                    request, f'Não foi possível criar a cobrança: {error}')

    return render(request, 'billing/subscription.html', {
        'title': 'Assinatura Evolutty',
        'subscription': subscription,
        'monthly_value': settings.ASAAS_MONTHLY_VALUE,
    })


@csrf_exempt
def asaas_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo nao permitido'}, status=405)

    expected_token = getattr(settings, 'ASAAS_WEBHOOK_TOKEN', '')
    received_token = request.headers.get('asaas-access-token', '')
    if not expected_token or received_token != expected_token:
        return JsonResponse({'error': 'Nao autorizado'}, status=401)

    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalido'}, status=400)

    event_type = payload.get('event', '')
    payment = payload.get('payment') or {}
    subscription_data = payload.get('subscription') or {}
    subscription_id = payment.get(
        'subscription') or subscription_data.get('id')
    event_id = request.headers.get('asaas-event-id') or payload.get('id')
    event_key = f'{event_type}:{event_id}'

    if not event_type or not event_id:
        return JsonResponse({'error': 'Evento sem identificador'}, status=400)

    with transaction.atomic():
        _, created = AsaasWebhookEvent.objects.get_or_create(
            event_key=event_key,
            defaults={'event_type': event_type, 'payload': payload},
        )
        if not created:
            return JsonResponse({'received': True, 'duplicate': True})

        if subscription_id:
            subscription = Subscription.objects.filter(
                asaas_subscription_id=subscription_id).first()
            if subscription:
                status_map = {
                    'PAYMENT_CONFIRMED': 'ACTIVE',
                    'PAYMENT_RECEIVED': 'ACTIVE',
                    'PAYMENT_OVERDUE': 'OVERDUE',
                    'PAYMENT_DELETED': 'OVERDUE',
                    'SUBSCRIPTION_CANCELED': 'CANCELED',
                }
                new_status = status_map.get(event_type)
                if new_status:
                    subscription.status = new_status
                if payment.get('dueDate'):
                    subscription.next_due_date = payment['dueDate']
                if payment.get('invoiceUrl') or payment.get('bankSlipUrl'):
                    subscription.payment_url = payment.get(
                        'invoiceUrl') or payment.get('bankSlipUrl')
                subscription.last_event_key = event_key
                subscription.save(update_fields=[
                    'status', 'next_due_date', 'payment_url', 'last_event_key', 'updated_at'])

    return JsonResponse({'received': True})
