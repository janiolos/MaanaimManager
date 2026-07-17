#!/bin/bash
# =============================================================
# deploy_containers.sh — Maanaim Manager
# Sobe cada container separadamente com logs para avaliação
# Uso: bash scripts/deploy_containers.sh [--clean]
# =============================================================

set -euo pipefail

# ── Cores ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Utilitários ────────────────────────────────────────────
log()   { echo -e "${CYAN}[$(date '+%H:%M:%S')]${RESET} $*"; }
ok()    { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✔ $*${RESET}"; }
warn()  { echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ $*${RESET}"; }
error() { echo -e "${RED}[$(date '+%H:%M:%S')] ✖ $*${RESET}"; }
sep()   { echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"; }

# ── Diretório raiz do projeto ──────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

log "Diretório do projeto: ${PROJECT_DIR}"

# ── Opções ─────────────────────────────────────────────────
CLEAN=false
if [[ "${1:-}" == "--clean" ]]; then
  CLEAN=true
  warn "Modo --clean: volumes e containers antigos serão removidos."
fi

# ── Pré-verificações ───────────────────────────────────────
sep
log "Verificando pré-requisitos..."

if ! command -v docker &>/dev/null; then
  error "Docker não encontrado. Instale antes de continuar."
  exit 1
fi

if ! command -v docker compose &>/dev/null 2>&1; then
  error "Docker Compose v2 não encontrado (esperado: 'docker compose')."
  exit 1
fi

if [[ ! -f ".env" ]]; then
  error "Arquivo .env não encontrado em ${PROJECT_DIR}"
  exit 1
fi

ok "Pré-requisitos OK"

# ── Limpeza opcional ───────────────────────────────────────
if $CLEAN; then
  sep
  warn "Parando e removendo containers/volumes antigos..."
  docker compose down -v --remove-orphans 2>&1 | sed 's/^/  /'
  ok "Limpeza concluída"
fi

# ══════════════════════════════════════════════════════════
# 1️⃣  CONTAINER: db (PostgreSQL)
# ══════════════════════════════════════════════════════════
sep
echo -e "${BOLD}${CYAN}1/3 — Subindo banco de dados (PostgreSQL)${RESET}"
sep

docker compose up -d db
log "Aguardando healthcheck do banco (máx 60s)..."

ELAPSED=0
until docker compose ps db | grep -q "healthy"; do
  if [[ $ELAPSED -ge 60 ]]; then
    error "Banco NÃO ficou saudável em 60s. Logs abaixo:"
    docker compose logs --tail=40 db
    exit 1
  fi
  echo -ne "  aguardando... ${ELAPSED}s\r"
  sleep 3
  ELAPSED=$((ELAPSED + 3))
done

ok "Banco de dados saudável!"
sep
log "📋 Logs do container DB (últimas 30 linhas):"
docker compose logs --tail=30 --no-log-prefix db | sed 's/^/  | /'

# ══════════════════════════════════════════════════════════
# 2️⃣  CONTAINER: app (Django + Gunicorn)
# ══════════════════════════════════════════════════════════
sep
echo -e "${BOLD}${CYAN}2/3 — Subindo aplicação Django (Gunicorn)${RESET}"
sep

docker compose up -d app
log "Aguardando healthcheck da aplicação (máx 120s)..."

ELAPSED=0
until docker compose ps app | grep -q "healthy"; do
  if [[ $ELAPSED -ge 120 ]]; then
    error "App NÃO ficou saudável em 120s. Logs abaixo:"
    docker compose logs --tail=60 app
    exit 1
  fi
  echo -ne "  aguardando... ${ELAPSED}s\r"
  sleep 5
  ELAPSED=$((ELAPSED + 5))
done

ok "Aplicação Django saudável!"
sep
log "📋 Logs do container APP (últimas 40 linhas):"
docker compose logs --tail=40 --no-log-prefix app | sed 's/^/  | /'

# ══════════════════════════════════════════════════════════
# 3️⃣  CONTAINER: caddy (Reverse Proxy)
# ══════════════════════════════════════════════════════════
sep
echo -e "${BOLD}${CYAN}3/3 — Subindo reverse proxy (Caddy)${RESET}"
sep

docker compose up -d caddy
log "Aguardando Caddy iniciar (máx 30s)..."
sleep 5

# Verifica se o caddy está running
if docker compose ps caddy | grep -qE "running|Up"; then
  ok "Caddy está rodando!"
else
  error "Caddy não iniciou corretamente. Logs:"
  docker compose logs --tail=40 caddy
  exit 1
fi

sep
log "📋 Logs do container CADDY (últimas 20 linhas):"
docker compose logs --tail=20 --no-log-prefix caddy | sed 's/^/  | /'

# ══════════════════════════════════════════════════════════
# Resumo Final
# ══════════════════════════════════════════════════════════
sep
echo -e "${BOLD}${GREEN}✅  DEPLOY CONCLUÍDO COM SUCESSO!${RESET}"
sep
echo ""
log "Status geral dos containers:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Lê HOST_PORT do .env
HOST_PORT=$(grep -E '^HOST_PORT=' .env | cut -d= -f2 | tr -d '"' | tr -d "'")
HOST_PORT="${HOST_PORT:-8080}"
DOMAIN=$(grep -E '^DOMAIN=' .env | cut -d= -f2 | tr -d '"' | tr -d "'")
DOMAIN="${DOMAIN:-localhost}"

echo -e "${BOLD}🌐 Acesse a aplicação em:${RESET}"
echo -e "   → http://${DOMAIN}:${HOST_PORT}"
echo ""
echo -e "${YELLOW}💡 Para acompanhar logs em tempo real de todos os containers:${RESET}"
echo -e "   docker compose logs -f"
echo ""
echo -e "${YELLOW}💡 Para logs de um container específico:${RESET}"
echo -e "   docker compose logs -f db"
echo -e "   docker compose logs -f app"
echo -e "   docker compose logs -f caddy"
sep
