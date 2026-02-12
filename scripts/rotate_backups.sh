#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

[[ -f .env ]] || { echo "[ERRO] Arquivo .env não encontrado."; exit 1; }
set -a
source .env
set +a

RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TARGET_DIR="./backups/db"

mkdir -p "$TARGET_DIR"

echo "[INFO] Removendo backups locais com mais de ${RETENTION_DAYS} dias..."
find "$TARGET_DIR" -type f -name '*.sql.gz' -mtime +"$RETENTION_DAYS" -print -delete

echo "[OK] Rotação concluída."
