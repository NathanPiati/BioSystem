#!/usr/bin/env python3
"""
Sistema Biométrico para Academia Evolutty

Este script demonstra como implementar reconhecimento facial
e de impressão digital no sistema de controle de acesso.

Pré-requisitos:
- Python 3.6+
- face-recognition (para reconhecimento facial)
- opencv-python
- numpy
- requests
- Conexão com o servidor Django

Para instalar dependências:
pip install face-recognition opencv-python numpy requests
"""

import requests
import base64
import json
import time
from io import BytesIO
from PIL import Image
import os

# Configurações do servidor
SERVER_URL = 'http://127.0.0.1:8000'  # Altere para o URL do seu servidor


class BiometricSystem:
    """Sistema biométrico para integração com Academia Evolutty"""

    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()

    def enroll_fingerprint(self, member_id, fingerprint_data):
        """
        Cadastra impressão digital de um aluno

        Args:
            member_id (int): ID do aluno
            fingerprint_data (bytes): Dados biométricos da impressão digital

        Returns:
            dict: Resultado do cadastro
        """
        try:
            # Codificar dados em base64
            encoded_data = base64.b64encode(fingerprint_data).decode()

            url = f"{self.server_url}/api/biometric/enroll-fingerprint/"
            data = {
                'member_id': member_id,
                'fingerprint_data': encoded_data
            }

            response = self.session.post(url, json=data)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro de conexão: {str(e)}'
            }

    def enroll_face(self, member_id, image_path):
        """
        Cadastra face de um aluno

        Args:
            member_id (int): ID do aluno
            image_path (str): Caminho para a imagem facial

        Returns:
            dict: Resultado do cadastro
        """
        try:
            # Ler e codificar imagem
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            url = f"{self.server_url}/api/biometric/enroll-face/"
            data = {
                'member_id': member_id,
                'face_image': f"data:image/jpeg;base64,{image_data}"
            }

            response = self.session.post(url, json=data)
            response.raise_for_status()

            return response.json()

        except FileNotFoundError:
            return {
                'success': False,
                'message': f'Imagem não encontrada: {image_path}'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro de conexão: {str(e)}'
            }

    def validate_fingerprint(self, fingerprint_data, turnstile_id='biometric_default'):
        """
        Valida acesso por impressão digital

        Args:
            fingerprint_data (bytes): Dados biométricos da impressão digital
            turnstile_id (str): ID da catraca

        Returns:
            dict: Resultado da validação
        """
        try:
            # Codificar dados em base64
            encoded_data = base64.b64encode(fingerprint_data).decode()

            url = f"{self.server_url}/api/biometric/validate-fingerprint/"
            data = {
                'fingerprint_data': encoded_data,
                'turnstile_id': turnstile_id
            }

            response = self.session.post(url, json=data)
            response.raise_for_status()

            return response.json()

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro de conexão: {str(e)}'
            }

    def validate_face(self, image_path, turnstile_id='biometric_default'):
        """
        Valida acesso por reconhecimento facial

        Args:
            image_path (str): Caminho para a imagem facial
            turnstile_id (str): ID da catraca

        Returns:
            dict: Resultado da validação
        """
        try:
            # Ler e codificar imagem
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()

            url = f"{self.server_url}/api/biometric/validate-face/"
            data = {
                'face_image': f"data:image/jpeg;base64,{image_data}",
                'turnstile_id': turnstile_id
            }

            response = self.session.post(url, json=data)
            response.raise_for_status()

            return response.json()

        except FileNotFoundError:
            return {
                'success': False,
                'message': f'Imagem não encontrada: {image_path}'
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Erro de conexão: {str(e)}'
            }


def simulate_biometric_enrollment():
    """Simula o cadastro biométrico de alunos"""

    print("🔐 Cadastro Biométrico - Academia Evolutty")
    print("=" * 50)

    bio_system = BiometricSystem(SERVER_URL)

    # Simular cadastro de impressão digital
    print("\n📱 Cadastrando impressão digital...")
    # Em produção, isso viria de um sensor biométrico real
    dummy_fingerprint = b"dummy_fingerprint_data_12345"

    result = bio_system.enroll_fingerprint(
        member_id=1, fingerprint_data=dummy_fingerprint)
    if result.get('success'):
        print("✅ Impressão digital cadastrada com sucesso!")
    else:
        print(f"❌ Erro: {result.get('message')}")

    # Simular cadastro facial
    print("\n📸 Cadastrando reconhecimento facial...")
    # Usar uma imagem de exemplo (você precisaria de uma imagem real)
    sample_image = "sample_face.jpg"

    if os.path.exists(sample_image):
        result = bio_system.enroll_face(member_id=1, image_path=sample_image)
        if result.get('success'):
            print("✅ Face cadastrada com sucesso!")
            print(".2f" else:
            print(f"❌ Erro: {result.get('message')}")
    else:
        print(f"⚠️  Imagem de exemplo não encontrada: {sample_image}")
        print("   Crie uma imagem sample_face.jpg para testar o reconhecimento facial")


def simulate_biometric_access():
    """Simula validação biométrica de acesso"""

    print("\n🚪 Validação Biométrica de Acesso")
    print("=" * 50)

    bio_system=BiometricSystem(SERVER_URL)

    # Simular validação por impressão digital
    print("\n👆 Testando validação por impressão digital...")
    dummy_fingerprint=b"dummy_fingerprint_data_12345"

    result=bio_system.validate_fingerprint(dummy_fingerprint)
    if result.get('success'):
        print("✅ Acesso permitido por impressão digital!")
        print(f"👤 Aluno: {result['member']['name']}")
        print(f"📋 Plano: {result['member']['plan']}")
        print(".2f" else:
        print(f"❌ Acesso negado: {result.get('message')}")

    # Simular validação facial
    print("\n📷 Testando validação facial...")
    sample_image="sample_face.jpg"

    if os.path.exists(sample_image):
        result=bio_system.validate_face(sample_image)
        if result.get('success'):
            print("✅ Acesso permitido por reconhecimento facial!")
            print(f"👤 Aluno: {result['member']['name']}")
            print(f"📋 Plano: {result['member']['plan']}")
            print(".2f" else:
            print(f"❌ Acesso negado: {result.get('message')}")
    else:
        print(f"⚠️  Imagem de exemplo não encontrada: {sample_image}")


def create_sample_image():
    """Cria uma imagem de exemplo para testes"""

    print("\n🖼️  Criando imagem de exemplo...")

    # Criar uma imagem simples para teste
    img=Image.new('RGB', (200, 200), color='lightblue')
    img.save('sample_face.jpg')

    print("✅ Imagem sample_face.jpg criada!")
    print("   ⚠️  Esta é apenas uma imagem de teste.")
    print("   Para uso real, use fotos de rostos reais.")


def main():
    """Função principal"""

    print("Sistema Biométrico - Academia Evolutty")
    print("Escolha uma opção:")
    print("1. Criar imagem de exemplo")
    print("2. Simular cadastro biométrico")
    print("3. Simular validação de acesso")
    print("4. Executar tudo (teste completo)")
    print("5. Sair")

    choice=input("\nOpção: ").strip()

    if choice == '1':
        create_sample_image()
    elif choice == '2':
        simulate_biometric_enrollment()
    elif choice == '3':
        simulate_biometric_access()
    elif choice == '4':
        create_sample_image()
        time.sleep(1)
        simulate_biometric_enrollment()
        time.sleep(2)
        simulate_biometric_access()
    else:
        print("Saindo...")
        return

    input("\nPressione Enter para continuar...")


if __name__ == '__main__':
    main()
