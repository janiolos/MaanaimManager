#!/usr/bin/env bash
set -euo pipefail

# Script para criar um evento inicial no CycloHub
# Uso: ./scripts/criar_evento.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY_CMD=$(cat <<'PY'
from apps.core.models import Evento, CentroCusto
from django.utils import timezone
from datetime import timedelta

# Garante que existe um centro de custo padrão
cc, _ = CentroCusto.objects.get_or_create(
    codigo="01", 
    defaults={"nome": "GERAL", "ativo": True}
)

# Verifica se já existe algum evento
if not Evento.objects.exists():
    data_inicio = timezone.now() + timedelta(days=30)
    data_fim = data_inicio + timedelta(days=3)
    
    evento = Evento.objects.create(
        nome="Evento Inicial de Teste",
        data_inicio=data_inicio,
        data_fim=data_fim,
        status="PLANEJADO",
        centro_custo=cc,
        taxa_base=50.00,
        taxa_trabalhador=25.00,
        adicional_chale=100.00
    )
    print(f"✅ Evento '{evento.nome}' criado com sucesso para {data_inicio.strftime('%d/%m/%Y')}.")
else:
    print("ℹ️ Já existem eventos cadastrados. Pulando criação do evento inicial.")
PY
)

if command -v docker >/dev/null 2>&1 && docker compose ps app >/dev/null 2>&1; then
  echo "[INFO] Criando evento inicial via container app..."
  docker compose exec -T app python manage.py shell -c "$PY_CMD"
else
  echo "[INFO] Criando evento inicial via ambiente local..."
  python manage.py shell -c "$PY_CMD"
fi
