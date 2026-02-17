#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ $# -ne 1 ]]; then
  echo "Uso: ./scripts/restore.sh /caminho/arquivo.sql.gz"
  exit 1
fi

BACKUP_FILE="$1"
[[ -f "$BACKUP_FILE" ]] || { echo "[ERRO] Arquivo não encontrado: $BACKUP_FILE"; exit 1; }
[[ -f .env ]] || { echo "[ERRO] Arquivo .env não encontrado."; exit 1; }

set -a
source .env
set +a

echo "[INFO] Parando app para restauração consistente..."
docker compose stop app

echo "[INFO] Limpando schema público..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"

echo "[INFO] Restaurando backup: $BACKUP_FILE"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1

echo "[INFO] Subindo app novamente..."
docker compose up -d app

echo "[OK] Restauração concluída com sucesso."
