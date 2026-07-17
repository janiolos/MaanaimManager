"""Garante default de criado_em em pos_localvenda.

Revision ID: 0007_pos_local_criado_em
Revises: 0006_fornecedor_criado_em
Create Date: 2026-07-15
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_pos_local_criado_em"
down_revision = "0006_fornecedor_criado_em"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE pos_localvenda
        ALTER COLUMN criado_em SET DEFAULT CURRENT_TIMESTAMP
        """
    )
    op.execute(
        """
        UPDATE pos_localvenda
        SET criado_em = CURRENT_TIMESTAMP
        WHERE criado_em IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE pos_localvenda
        ALTER COLUMN criado_em DROP DEFAULT
        """
    )
