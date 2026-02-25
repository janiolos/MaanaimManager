#!/usr/bin/env bash
set -euo pipefail

# Script de Provisionamento de Novos Clientes (CycloHub SaaS)
# Uso: ./scripts/provision_client.sh <NOME_CLIENTE> <DOMINIO> <PORTA_HOST>

if [ "$#" -ne 3 ]; then
    echo "Uso: $0 <NOME_CLIENTE> <DOMINIO> <PORTA_HOST>"
    exit 1
fi

CLIENT_NAME=$1
DOMAIN=$2
HOST_PORT=$3
BASE_DIR="/opt/cyclohub/clients/${CLIENT_NAME}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Iniciando provisionamento para o cliente: ${CLIENT_NAME}"

# 1. Criar estrutura de diretórios
if [ -d "${BASE_DIR}" ]; then
    echo "⚠️ Erro: O diretório ${BASE_DIR} já existe."
    exit 1
fi

sudo mkdir -p "${BASE_DIR}"
sudo chown -R $(whoami):$(whoami) "${BASE_DIR}"

# 2. Copiar arquivos base
echo "📂 Copiando arquivos base..."
cp -r "${REPO_DIR}/." "${BASE_DIR}/"

# 3. Gerar .env customizado
echo "📝 Gerando arquivo .env..."
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')
DB_PASS=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')

cat <<EOF > "${BASE_DIR}/.env"
PROJECT_NAME=${CLIENT_NAME}
APP_SECRET_KEY=${SECRET_KEY}
APP_ALLOWED_HOSTS=${DOMAIN},localhost,127.0.0.1
HOST_PORT=${HOST_PORT}
POSTGRES_DB=eventa_${CLIENT_NAME}
POSTGRES_USER=user_${CLIENT_NAME}
POSTGRES_PASSWORD=${DB_PASS}
ADMIN_EMAIL=admin@${DOMAIN}
APP_PORT=8000
TIMEZONE=America/Sao_Paulo
APP_ENV=prod

# S3 Storage (Opcional)
USE_S3=0
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_ENDPOINT_URL=
AWS_S3_REGION_NAME=auto
AWS_S3_CUSTOM_DOMAIN=
EOF

# 4. Criar pastas de dados
mkdir -p "${BASE_DIR}/data/postgres" "${BASE_DIR}/media"

# 5. Subir a stack
echo "🐳 Subindo containers para ${CLIENT_NAME} na porta ${HOST_PORT}..."
cd "${BASE_DIR}"
# Garantir que o docker compose veja o .env local
docker compose --env-file .env up -d --build

echo "✅ Cliente ${CLIENT_NAME} provisionado com sucesso!"
echo "🔗 Acesso via: http://${DOMAIN} (Porta exposta: ${HOST_PORT})"
echo "📂 Pastas localizadas em: ${BASE_DIR}"
