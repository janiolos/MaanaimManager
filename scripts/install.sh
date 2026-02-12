#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

info() { echo "[INFO] $*"; }
warn() { echo "[AVISO] $*"; }
err() { echo "[ERRO] $*"; }

if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
else
  SUDO=""
fi

command -v apt-get >/dev/null 2>&1 || {
  err "Este instalador suporta Debian/Ubuntu (apt)."
  exit 1
}

if ! command -v docker >/dev/null 2>&1; then
  info "Instalando Docker..."
  $SUDO apt-get update -y
  $SUDO apt-get install -y ca-certificates curl gnupg lsb-release
  $SUDO install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") $(. /etc/os-release; echo "$VERSION_CODENAME") stable" \
    | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
  $SUDO apt-get update -y
  $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  $SUDO systemctl enable docker
  $SUDO systemctl start docker
else
  info "Docker já instalado."
fi

if ! docker compose version >/dev/null 2>&1; then
  err "Docker Compose plugin não encontrado."
  exit 1
fi

mkdir -p ./data/postgres ./data/static ./backups ./media
chmod 700 ./data/postgres
chmod 755 ./backups ./media ./data/static
$SUDO chown -R 999:999 ./data/postgres || true
chmod 644 ./caddy/Caddyfile || true

if [[ ! -f .env ]]; then
  cp .env.example .env
  warn "Arquivo .env criado a partir de .env.example."
  warn "Edite o arquivo .env antes de produção (senhas, domínio e chave secreta)."
else
  info ".env já existe, mantendo arquivo atual."
fi

info "Subindo stack..."
docker compose up -d --build

cat <<MSG

Stack iniciada com sucesso.

Comandos úteis:
- Status:         docker compose ps
- Logs app:       docker compose logs -f app
- Logs caddy:     docker compose logs -f caddy
- Healthcheck:    ./scripts/healthcheck.sh

MSG
