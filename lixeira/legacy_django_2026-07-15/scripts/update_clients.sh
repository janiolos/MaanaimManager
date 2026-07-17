#!/usr/bin/env bash
set -euo pipefail

# Script de Atualização Global de Clientes (CycloHub SaaS)
# Sincroniza o código central (source) com todas as pastas de clientes e reinicia os containers.

SOURCE_DIR="/opt/cyclohub/source"
CLIENTS_DIR="/opt/cyclohub/clients"

echo "🔄 Iniciando atualização global dos clientes..."

if [ ! -d "$CLIENTS_DIR" ]; then
    echo "⚠️ Nenhum cliente encontrado em $CLIENTS_DIR"
    exit 0
fi

# 1. Garantir que o source está atualizado (opcional, assumimos que o usuário já deu git pull)
# cd "$SOURCE_DIR" && git pull

for client_path in "$CLIENTS_DIR"/*; do
    if [ -d "$client_path" ] && [ -f "$client_path/docker-compose.yml" ]; then
        client_name=$(basename "$client_path")
        echo "Updating client: $client_name..."

        # Sincronizar apenas arquivos de código, ignorando .env e pastas de dados
        # Usamos rsync para ser eficiente
        rsync -av --progress "$SOURCE_DIR/" "$client_path/" \
            --exclude '.git' \
            --exclude '.env' \
            --exclude 'data/' \
            --exclude 'media/' \
            --exclude 'staticfiles/' \
            --exclude '__pycache__/'

        echo "🚀 Reiniciando containers para $client_name..."
        cd "$client_path"
        docker compose up -d --build
        echo "✅ $client_name atualizado!"
    fi
done

echo "🏁 Todos os clientes foram atualizados com sucesso."
