#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p backups

echo "[INFO] Baixando a pasta de backups do banco de dados do servidor remoto..."
echo "[INFO] Por favor, insira a senha do servidor quando solicitado."
scp -r root@cyclohub.com.br:/opt/cyclohub/clients/maanaim/backups/db/ backups/

echo "[OK] Download concluído! Backups disponíveis localmente:"
ls -la backups/db/
