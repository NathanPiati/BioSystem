import re

import requests
from django.conf import settings


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
        f'*Ficha de treino: {workout.name}*',
        f'Cliente: {workout.client}',
        f'Personal: {workout.personal}',
    ]
    if workout.goal:
        lines.append(f'Objetivo: {workout.goal}')

    lines.append('')
    lines.append('*Exercícios*')
    exercises = workout.exercises.all()
    for exercise in exercises:
        load = exercise.load or 'sem carga'
        lines.append(
            f'{exercise.order}. {exercise.name} | '
            f'{exercise.sets} séries x {exercise.reps} | '
            f'Carga: {load} | Descanso: {exercise.rest_seconds}s'
        )

    if workout.notes:
        lines.extend(['', f'*Observações:* {workout.notes}'])
    lines.extend(['', 'Evolutty - Portal Personal Trainer'])
    return '\n'.join(lines)


def send_workout_message(workout):
    api_url = getattr(settings, 'EVOLUTION_API_URL', '').rstrip('/')
    api_key = getattr(settings, 'EVOLUTION_API_KEY', '')
    instance = getattr(settings, 'EVOLUTION_API_INSTANCE', '')
    if not api_url or not api_key or not instance:
        raise EvolutionAPIError(
            'A Evolution API não está configurada. Defina '
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
