#!/usr/bin/env python3
"""
Exemplo de integração com catraca para Academia BioSystem

Este script demonstra como uma catraca física pode se integrar
com o sistema Django para validar acessos de alunos.

Pré-requisitos:
- Python 3.6+
- requests library
- Conexão com o servidor Django

Uso:
python turnstile_example.py
"""

import requests
import time
import json
from datetime import datetime

# Configurações do servidor
SERVER_URL = 'http://127.0.0.1:8000'  # Altere para o URL do seu servidor
TURNSTILE_ID = 'entrance_main'  # ID único da catraca


class TurnstileController:
    """Controlador de catraca para integração com Academia BioSystem"""

    def __init__(self, server_url, turnstile_id):
        self.server_url = server_url.rstrip('/')
        self.turnstile_id = turnstile_id

    def validate_access(self, card_id):
        """
        Valida se um cartão tem permissão de acesso

        Args:
            card_id (str): ID do cartão RFID/código de barras

        Returns:
            dict: Resultado da validação com dados do aluno ou erro
        """
        try:
            url = f"{self.server_url}/api/turnstile/validate-access/"
            params = {
                'card_id': card_id,
                'turnstile_id': self.turnstile_id
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro de conexão: {str(e)}'
            }

    def register_exit(self, card_id):
        """
        Registra a saída de um aluno

        Args:
            card_id (str): ID do cartão do aluno

        Returns:
            dict: Confirmação do registro
        """
        try:
            url = f"{self.server_url}/api/turnstile/register-exit/"
            params = {
                'card_id': card_id,
                'turnstile_id': self.turnstile_id
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro ao registrar saída: {str(e)}'
            }

    def get_access_logs(self, member_id=None, date_from=None, date_to=None, limit=50):
        """
        Consulta logs de acesso

        Args:
            member_id (int, optional): ID do aluno
            date_from (str, optional): Data inicial (YYYY-MM-DD)
            date_to (str, optional): Data final (YYYY-MM-DD)
            limit (int): Número máximo de registros

        Returns:
            dict: Logs de acesso
        """
        try:
            url = f"{self.server_url}/api/turnstile/access-logs/"
            params = {'limit': limit}

            if member_id:
                params['member_id'] = member_id
            if date_from:
                params['date_from'] = date_from
            if date_to:
                params['date_to'] = date_to

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro ao consultar logs: {str(e)}'
            }


def simulate_turnstile():
    """Simulação de funcionamento de uma catraca"""

    print("🚪 Simulador de Catraca - Academia BioSystem")
    print("=" * 50)

    # Inicializar controlador
    turnstile = TurnstileController(SERVER_URL, TURNSTILE_ID)

    # Exemplos de cartões para teste
    test_cards = [
        'CARD001',  # Cartão válido
        'CARD002',  # Cartão válido
        'INVALID',  # Cartão inválido
        'CARD001',  # Teste de saída
    ]

    for card_id in test_cards:
        print(f"\n🔍 Lendo cartão: {card_id}")
        print("-" * 30)

        # Simular leitura do cartão
        time.sleep(1)

        # Validar acesso
        result = turnstile.validate_access(card_id)

        if result.get('success'):
            print("✅ ACESSO PERMITIDO" print(f"👤 Aluno: {result['member']['name']}")
            print(f"📋 Plano: {result['member']['plan']}")
            print(f"📅 Vencimento: {result['member']['enrollment_end']}")

            # Simular abertura da catraca
            print("🚪 Catraca liberada - Entrada permitida")
            time.sleep(2)

            # Registrar saída após alguns segundos
            print(f"\n📤 Registrando saída para {card_id}...")
            exit_result=turnstile.register_exit(card_id)
            if exit_result.get('success'):
                print("✅ Saída registrada com sucesso")
            else:
                print(
                    f"❌ Erro ao registrar saída: {exit_result.get('message')}")

        else:
            print("❌ ACESSO NEGADO" print(f"📝 Motivo: {result.get('message', 'Erro desconhecido')}")

            # Manter catraca fechada
            print("🚪 Catraca permanece fechada")

        print("-" * 30)
        time.sleep(2)

    # Exibir logs recentes
    print("
📊 Logs de acesso recentes:"    logs = turnstile.get_access_logs(limit=10)

    if logs.get('success'):
        for log in logs.get('logs', []):
            timestamp = log['timestamp'][:19]  # Formatar data/hora
            status = "✅" if log['success'] else "❌"
            tipo = "Entrada" if log['access_type'] == 'entry' else "Saída"
            print(f"{status} {timestamp} - {log['member_name']} - {tipo}")
    else:
        print(f"Erro ao consultar logs: {logs.get('message')}")


def test_api_endpoints():
    """Testa todos os endpoints da API"""

    print("🧪 Testando endpoints da API...")
    print("=" * 50)

    turnstile = TurnstileController(SERVER_URL, TURNSTILE_ID)

    # Teste 1: Cartão válido
    print("Teste 1: Cartão válido")
    result = turnstile.validate_access('CARD001')
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")

    # Teste 2: Cartão inválido
    print("\nTeste 2: Cartão inválido")
    result = turnstile.validate_access('INVALID')
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")

    # Teste 3: Consulta de logs
    print("\nTeste 3: Consulta de logs")
    result = turnstile.get_access_logs(limit=5)
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == '__main__':
    print("Escolha uma opção:")
    print("1. Simular funcionamento da catraca")
    print("2. Testar endpoints da API")
    print("3. Sair")

    choice = input("Opção: ").strip()

    if choice == '1':
        simulate_turnstile()
    elif choice == '2':
        test_api_endpoints()
    else:
        print("Saindo...")