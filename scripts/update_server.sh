#!/usr/bin/env bash
set -euo pipefail

# Script to update cyclohub server to MaanaimManager v2 (FastAPI + React)
# This script runs on the remote server 'cyclohub.com.br'.

CLIENTS_DIR="/opt/cyclohub/clients"
SOURCE_DIR="/opt/cyclohub/source"

echo "🔄 Starting update to MaanaimManager v2..."

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <client_name>"
    echo "Example: $0 maanaim"
    exit 1
fi

CLIENT_NAME=$1
CLIENT_PATH="${CLIENTS_DIR}/${CLIENT_NAME}"

if [ ! -d "$CLIENT_PATH" ]; then
    echo "❌ Client directory not found: $CLIENT_PATH"
    exit 1
fi

# 1. Update source directory
echo "📦 Updating source directory at $SOURCE_DIR..."
cd "$SOURCE_DIR"
git pull

# 2. Stop legacy Django containers
if [ -f "${CLIENT_PATH}/docker-compose.yml" ]; then
    echo "🛑 Stopping legacy Django containers for ${CLIENT_NAME}..."
    docker compose -f "${CLIENT_PATH}/docker-compose.yml" down || true
    # Rename legacy compose file to prevent accidental runs
    mv "${CLIENT_PATH}/docker-compose.yml" "${CLIENT_PATH}/docker-compose.legacy.yml"
fi

# 3. Sync files from source to client directory
echo "📂 Syncing v2 files to ${CLIENT_NAME}..."
rsync -av --progress "${SOURCE_DIR}/" "${CLIENT_PATH}/" \
    --exclude '.git' \
    --exclude '.env' \
    --exclude 'data/' \
    --exclude 'media/' \
    --exclude 'staticfiles/' \
    --exclude '__pycache__/'

# 4. Update client's .env file with new variables if missing
ENV_FILE="${CLIENT_PATH}/.env"
if [ -f "$ENV_FILE" ]; then
    echo "📝 Checking .env configuration..."
    
    # Check if JWT_SECRET_KEY is present
    if ! grep -q "JWT_SECRET_KEY" "$ENV_FILE"; then
        echo "🔑 Generating JWT_SECRET_KEY..."
        JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        echo "" >> "$ENV_FILE"
        echo "# --- Maanaim Manager v2 (FastAPI + React) Additions ---" >> "$ENV_FILE"
        echo "JWT_SECRET_KEY=${JWT_SECRET}" >> "$ENV_FILE"
    fi

    # Check if BACKEND_CORS_ORIGINS is present
    if ! grep -q "BACKEND_CORS_ORIGINS" "$ENV_FILE"; then
        echo "🌐 Adding BACKEND_CORS_ORIGINS..."
        DOMAIN=$(grep "APP_ALLOWED_HOSTS" "$ENV_FILE" | cut -d'=' -f2 | cut -d',' -f1 || echo "localhost")
        echo "BACKEND_CORS_ORIGINS=[\"http://${DOMAIN}\",\"https://${DOMAIN}\"]" >> "$ENV_FILE"
    fi
else
    echo "❌ .env file not found for client! Please create it."
    exit 1
fi

# 5. Build and start the new containers
echo "🐳 Building and starting new FastAPI + React stack..."
cd "$CLIENT_PATH"
docker compose -f docker-compose.v2.yml build
docker compose -f docker-compose.v2.yml up -d

# 6. Run database migrations
echo "🗄️ Running database migrations..."
# Wait a moment for database container to be healthy
sleep 5
docker compose -f docker-compose.v2.yml exec -T backend alembic upgrade head

echo "✅ ${CLIENT_NAME} updated to MaanaimManager v2 successfully!"
