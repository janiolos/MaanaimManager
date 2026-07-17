#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

[[ -f .env ]] || { echo "[ERRO] Arquivo .env não encontrado."; exit 1; }
set -a
source .env
set +a

if [ -z "${1:-}" ]; then
  echo "Uso: $0 <caminho_do_backup.sql.gz>"
  exit 1
fi

BACKUP_FILE=$1

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "[ERRO] Arquivo de backup não encontrado: $BACKUP_FILE"
  exit 1
fi

echo "[INFO] Restaurando $BACKUP_FILE no banco de dados local (${POSTGRES_DB})..."

echo "[INFO] Recriando banco de dados (forçando desconexão de sessões ativas)..."
docker compose -f docker-compose.v2.yml exec -T db dropdb -U "$POSTGRES_USER" --force --if-exists "$POSTGRES_DB"
docker compose -f docker-compose.v2.yml exec -T db createdb -U "$POSTGRES_USER" "$POSTGRES_DB"

echo "[INFO] Importando dados..."
gunzip -c "$BACKUP_FILE" | docker compose -f docker-compose.v2.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "[OK] Restauração concluída!"
