import re

import requests
from django.conf import settings

from .models import PersonalWhatsAppConfig


class EvolutionAPIError(Exception):
    """Erro esperado ao enviar uma mensagem pela Evolution API."""


def _whatsapp_number(phone):
    number = re.sub(r'\D', '', phone or '')
    if len(number) in (10, 11):
        number = f'55{number}'
    if not number or len(number) < 12:
        raise EvolutionAPIError(
            'O telefone do cliente não está em formato válido.')
    return number


def build_workout_message(workout):
    lines = [
        '🏋️ *EVOLUTTY | FICHA DE TREINO*',
        '━━━━━━━━━━━━━━━━━━━━',
        f'*Treino:* {workout.name}',
        f'*Aluno:* {workout.client}',
        f'*Personal:* {workout.personal}',
    ]
    if workout.goal:
        lines.append(f'*Objetivo:* {workout.goal}')

    lines.extend(['', '*📋 EXERCÍCIOS*', ''])
    exercises = workout.exercises.all()
    for exercise in exercises:
        lines.extend([
            f'*{exercise.order:02d} · {exercise.name}*',
            f'   • {exercise.sets} séries × {exercise.reps} repetições',
            f'   • Carga: {exercise.load or "Peso livre"}',
            f'   • Descanso: {exercise.rest_seconds}s',
            '',
        ])

    if workout.notes:
        lines.extend(['*📝 OBSERVAÇÕES*', workout.notes, ''])
    lines.extend([
        '━━━━━━━━━━━━━━━━━━━━',
        '💪 Bons treinos e evolução constante!',
        '_Enviado pelo Evolutty_',
    ])
    return '\n'.join(lines)


def send_workout_message(workout):
    config = getattr(workout.personal, 'whatsapp_config', None)
    if config is None and hasattr(workout.personal, 'pk'):
        config = PersonalWhatsAppConfig.objects.filter(
            personal_id=workout.personal.pk).first()

    if config is not None:
        if not config.enabled or not config.send_workout_messages:
            raise EvolutionAPIError(
                'O envio de fichas está desativado para este personal.')
        api_url = config.api_url.rstrip('/')
        api_key = config.api_key
        instance = config.instance_name
    else:
        api_url = getattr(settings, 'EVOLUTION_API_URL', '').rstrip('/')
        api_key = getattr(settings, 'EVOLUTION_API_KEY', '')
        instance = getattr(settings, 'EVOLUTION_API_INSTANCE', '')
    if not api_url or not api_key or not instance:
        raise EvolutionAPIError(
            'A Evolution API não está configurada. Defina '
            'a configuração do WhatsApp do personal ou as variáveis '
            'EVOLUTION_API_URL, EVOLUTION_API_KEY e EVOLUTION_API_INSTANCE.'
        )

    endpoint = f'{api_url}/message/sendText/{instance}'
    payload = {
        'number': _whatsapp_number(workout.client.phone),
        'text': build_workout_message(workout),
    }
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={'apikey': api_key, 'Content-Type': 'application/json'},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        detail = ''
        if getattr(exc, 'response', None) is not None:
            detail = f' Resposta: {exc.response.text[:200]}'
        raise EvolutionAPIError(
            f'Não foi possível enviar a ficha pelo WhatsApp.{detail}'
        ) from exc
