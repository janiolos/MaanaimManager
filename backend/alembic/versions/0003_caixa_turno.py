"""Adiciona controle de caixa (turno) em LocalVenda.

Revision ID: 0003_caixa_turno
Revises: 0002_fase_a_pos_estoque_config
Create Date: 2026-07-14 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_caixa_turno"
down_revision: Union[str, None] = "0002_fase_a_pos_estoque_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pos_localvenda",
        sa.Column("caixa_aberto", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "pos_localvenda",
        sa.Column("caixa_aberto_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "pos_localvenda",
        sa.Column("caixa_aberto_por_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_local_caixa_aberto_por",
        "pos_localvenda",
        "auth_user",
        ["caixa_aberto_por_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_local_caixa_aberto_por", "pos_localvenda", type_="foreignkey")
    op.drop_column("pos_localvenda", "caixa_aberto_por_id")
    op.drop_column("pos_localvenda", "caixa_aberto_em")
    op.drop_column("pos_localvenda", "caixa_aberto")
