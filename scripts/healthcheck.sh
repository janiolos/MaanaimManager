#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

set +e
echo "[INFO] Estado dos containers"
docker compose ps
PS_EXIT=$?
set -e

if [[ $PS_EXIT -ne 0 ]]; then
  echo "[ERRO] Falha ao consultar containers."
  exit 1
fi

echo "[INFO] Testando Postgres (pg_isready)..."
docker compose exec -T db pg_isready -U "${POSTGRES_USER:-eventa}" -d "${POSTGRES_DB:-eventa}" >/dev/null

echo "[INFO] Testando app (endpoint /login/)..."
if ! docker compose exec -T app sh -c 'curl -fsS "http://127.0.0.1:${APP_PORT:-8000}/login/" >/dev/null'; then
  echo "[ERRO] App não respondeu corretamente."
  exit 1
fi

echo "[INFO] Testando proxy local (http://localhost)..."
if ! curl -fsS http://localhost >/dev/null; then
  echo "[ERRO] Caddy não respondeu em http://localhost."
  exit 1
fi

echo "[OK] Healthcheck geral aprovado."
