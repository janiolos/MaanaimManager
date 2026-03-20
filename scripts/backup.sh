#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

[[ -f .env ]] || { echo "[ERRO] Arquivo .env não encontrado."; exit 1; }
set -a
source .env
set +a

PROJECT_NAME="${PROJECT_NAME:-eventa}"
BACKUP_DIR_HOST="./backups/db"
TIMESTAMP="$(date +%Y%m%d_%H%M)"
OUT_FILE="${BACKUP_DIR_HOST}/${TIMESTAMP}_${PROJECT_NAME}.sql.gz"

mkdir -p "$BACKUP_DIR_HOST"

echo "[INFO] Iniciando backup do banco..."
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip -c > "$OUT_FILE"

if [[ ! -s "$OUT_FILE" ]]; then
  echo "[ERRO] Backup inválido: arquivo vazio ou inexistente."
  rm -f "$OUT_FILE"
  exit 1
fi

echo "[INFO] Backup local criado: $OUT_FILE"

if [[ -n "${BACKUP_S3_BUCKET:-}" ]]; then
  if command -v aws >/dev/null 2>&1; then
    AWS_ARGS=()
    [[ -n "${AWS_ENDPOINT_URL:-}" ]] && AWS_ARGS+=(--endpoint-url "$AWS_ENDPOINT_URL")
    aws s3 cp "$OUT_FILE" "s3://${BACKUP_S3_BUCKET}/db/$(basename "$OUT_FILE")" "${AWS_ARGS[@]}"
    echo "[INFO] Backup enviado para S3: s3://${BACKUP_S3_BUCKET}/db/$(basename "$OUT_FILE")"
  else
    echo "[ERRO] BACKUP_S3_BUCKET definido, mas awscli não está instalado."
    exit 1
  fi
fi

echo "[OK] Backup concluído."
