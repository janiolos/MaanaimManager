"""Baseline do schema Django legado (sem alterações).

Para gerar esta primeira revisão, recomendado:
    alembic revision -m "baseline legacy" --autogenerate
e em seguida INSERIR um `op.execute("SELECT 1")` no upgrade para torná-la noop,
comentando as operações geradas (preservamos o schema existente).

Depois:
    alembic stamp head

Isto marca a base como já aplicada sem rodar DDL - o schema Django permanece intacto.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-13 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Baseline noop - schema já existe no Postgres legado.
    # Para gerar schema novo em ambiente limpo, use:
    #   alembic revision --autogenerate -m "..."  (após esta baseline)
    pass


def downgrade() -> None:
    # Não derrubamos tabelas Django legado.
    pass