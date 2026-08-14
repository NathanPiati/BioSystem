# Academia Evolutty

Projeto Django para gestão de academias e personal trainers com PostgreSQL, integração com catracas e **reconhecimento biométrico** (impressão digital e facial).

## Funcionalidades

- ✅ Cadastro de alunos com endereço completo e ID de cartão
- ✅ Busca automática de endereço por CEP (ViaCEP API)
- ✅ Gestão de planos de academia
- ✅ Controle de matrículas
- ✅ **Integração com Catracas** - Controle de acesso físico
- ✅ **Biometria Facial** - Reconhecimento facial para acesso
- ✅ **Impressão Digital** - Validação por digitais
- ✅ Logs detalhados de entrada/saída com método de autenticação
- ✅ Área administrativa completa
- ✅ Sistema de autenticação
- ✅ Interface responsiva e moderna

## Biometria

### Métodos Suportados

#### 🖼️ **Reconhecimento Facial**
- **Biblioteca**: `face-recognition` (dlib + OpenCV)
- **Precisão**: Comparação de encodings faciais
- **Cadastro**: Upload de foto via interface web
- **Validação**: Processamento em tempo real

#### 👆 **Impressão Digital**
- **Armazenamento**: Templates biométricos em base64
- **Validação**: Comparação de padrões digitais
- **Integração**: Compatível com sensores USB/serial
- **Segurança**: Dados criptografados no banco

### APIs Biométricas

#### Cadastro
```
POST /api/biometric/enroll-fingerprint/
{
    "member_id": 1,
    "fingerprint_data": "base64_encoded_data"
}

POST /api/biometric/enroll-face/
{
    "member_id": 1,
    "face_image": "data:image/jpeg;base64,..."
}
```

#### Validação
```
POST /api/biometric/validate-fingerprint/
{
    "fingerprint_data": "base64_encoded_data",
    "turnstile_id": "main_entrance"
}

POST /api/biometric/validate-face/
{
    "face_image": "data:image/jpeg;base64,...",
    "turnstile_id": "main_entrance"
}
```

### Configuração Biométrica

1. **Ativar biometria** no cadastro do aluno
2. **Upload de foto** para reconhecimento facial
3. **Cadastro de digital** via sensor biométrico
4. **Testar validação** usando as APIs

### Script de Demonstração

Execute o script `biometric_system.py` para testar:

```bash
python biometric_system.py
```

Este script inclui:
- Simulação completa de cadastro biométrico
- Testes de validação facial e digital
- Criação de imagens de exemplo
- Tratamento de erros e logs detalhados

## Integração com Catracas

### Como Funciona
1. **Cadastro do Cartão**: Cada aluno recebe um cartão RFID ou código de barras
2. **Validação de Acesso**: A catraca consulta a API para verificar se o aluno tem matrícula ativa
3. **Registro de Logs**: Todas as tentativas de acesso são registradas (permitidas ou negadas)
4. **Relatórios**: Visualize logs de acesso por aluno, data e catraca

### APIs Disponíveis

#### Validação de Acesso
```
GET /api/turnstile/validate-access/?card_id=ABC123&turnstile_id=entrance1
```
- **Parâmetros**: `card_id` (obrigatório), `turnstile_id` (opcional)
- **Resposta**: Status do acesso e dados do aluno

#### Registro de Saída
```
GET /api/turnstile/register-exit/?card_id=ABC123&turnstile_id=entrance1
```
- **Parâmetros**: `card_id` (obrigatório), `turnstile_id` (opcional)
- **Resposta**: Confirmação de saída registrada

#### Consulta de Logs
```
GET /api/turnstile/access-logs/?member_id=1&date_from=2024-01-01&date_to=2024-12-31
```
- **Parâmetros**: `member_id`, `date_from`, `date_to`, `limit`
- **Resposta**: Lista de logs de acesso

### Exemplo de Integração com Catraca

```python
# Exemplo em Python para catraca
import requests

def validate_card(card_id, turnstile_id='main'):
    response = requests.get(
        'http://seuservidor.com/api/turnstile/validate-access/',
        params={'card_id': card_id, 'turnstile_id': turnstile_id}
    )
    data = response.json()

    if data['success']:
        # Liberar catraca
        print(f"Acesso permitido para {data['member']['name']}")
        return True
    else:
        # Bloquear acesso
        print(f"Acesso negado: {data['message']}")
        return False
```

### Script de Exemplo

Execute o script `turnstile_example.py` para testar a integração:

```bash
python turnstile_example.py
```

Este script inclui:
- Simulação completa de catraca
- Testes de todos os endpoints
- Exemplos de tratamento de erros
- Consulta de logs de acesso

## Configuração de Cartões

### Cadastrando Cartões para Alunos

1. **Acesse o cadastro de alunos**: `http://127.0.0.1:8000/members/new/`
2. **Preencha os dados pessoais** do aluno
3. **Adicione o ID do cartão** no campo "ID do Cartão"
   - Para cartões RFID: Use o código único do cartão
   - Para códigos de barras: Use o número do código
4. **Salve o cadastro**

### Tipos de Identificação Suportados

- **Cartões RFID**: Códigos alfanuméricos únicos
- **Códigos de barras**: Números sequenciais
- **Cartões magnéticos**: Códigos específicos do fabricante
- **Biometria**: Pode ser integrada futuramente

### Segurança

- Cada cartão deve ser único no sistema
- O sistema valida automaticamente matrículas ativas
- Todos os acessos são registrados em log
- Tentativas de acesso inválido são bloqueadas e registradas

## Setup inicial

1. Ative o ambiente virtual:
   - Windows PowerShell: `.\.venv\Scripts\Activate.ps1`

2. Instale dependências:
   - `pip install -r requirements.txt`

3. Aplique migrações:
   - `python manage.py migrate`

4. Crie superusuário:
   - `python manage.py createsuperuser`

5. Execute o servidor:
   - `python manage.py runserver`

## Configuração do banco

O projeto já está configurado para usar PostgreSQL com:
- database: `AcademiaDB`
- user: `biosystem_user`
- password: `Inovatech2025@`

Se necessário, atualize `biosystem/settings.py`.

## Acesso

- Página inicial: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`

## API de CEP

A aplicação utiliza a API do ViaCEP para busca automática de endereços:
- Endpoint: `/api/search-zip-code/?zip_code=00000000`
- Formato: JSON
- Campos retornados: rua, bairro, cidade, estado

## Envio de ficha pelo WhatsApp

O detalhe de cada treino possui a ação **Enviar WhatsApp**, que envia ao telefone
cadastrado do cliente uma mensagem formatada com objetivo, exercícios, séries,
repetições, carga, descanso e observações.

Configure no `.env` do servidor os dados da instância da Evolution API:

```env
EVOLUTION_API_URL=https://seu-servidor-evolution.example.com
EVOLUTION_API_KEY=sua-chave-da-evolution-api
EVOLUTION_API_INSTANCE=nome-da-instancia
```

O telefone deve conter o DDD. Números brasileiros com 10 ou 11 dígitos recebem
automaticamente o código do país `55`; números internacionais devem ser salvos
já com o código do país.
