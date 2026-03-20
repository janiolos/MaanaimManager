#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GRUPOS=(
  "ADMINISTRADOR"
  "COORDENADOR"
  "FINANCEIRO"
  "FINANCEIRO_LEITURA"
  "ESTOQUE"
  "ESTOQUE_LEITURA"
  "HOSPEDAGEM"
  "HOSPEDAGEM_LEITURA"
  "MENSAGENS"
  "MENSAGENS_LEITURA"
  "VISUALIZACAO"
)

PY_CMD=$(cat <<'PY'
from django.contrib.auth.models import Group

grupos = [
    "ADMINISTRADOR",
    "COORDENADOR",
    "FINANCEIRO",
    "FINANCEIRO_LEITURA",
    "ESTOQUE",
    "ESTOQUE_LEITURA",
    "HOSPEDAGEM",
    "HOSPEDAGEM_LEITURA",
    "MENSAGENS",
    "MENSAGENS_LEITURA",
    "VISUALIZACAO",
]

for nome in grupos:
    Group.objects.get_or_create(name=nome)

print("Grupos criados/validados com sucesso:")
for nome in Group.objects.filter(name__in=grupos).order_by("name").values_list("name", flat=True):
    print(f"- {nome}")
PY
)

if command -v docker >/dev/null 2>&1 && docker compose ps app >/dev/null 2>&1; then
  echo "[INFO] Criando grupos via container app..."
  docker compose exec -T app python manage.py shell -c "$PY_CMD"
else
  echo "[INFO] Criando grupos via ambiente local..."
  python manage.py shell -c "$PY_CMD"
fi
