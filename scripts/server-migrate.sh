#!/bin/bash
# Setup de ambiente virtual e migrate no servidor (sem Docker).
# Uso: bash scripts/server-migrate.sh

set -e

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

echo "Rodando migrate..."
python manage.py migrate

echo "Concluido."
