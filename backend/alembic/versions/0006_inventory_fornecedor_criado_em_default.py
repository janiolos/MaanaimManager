"""Garante default de criado_em em inventory_fornecedor.

Revision ID: 0006_fornecedor_criado_em
Revises: 0005_integridade_estoque_pdv
Create Date: 2026-07-15
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_fornecedor_criado_em"
down_revision = "0005_integridade_estoque_pdv"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE inventory_fornecedor
        ALTER COLUMN criado_em SET DEFAULT CURRENT_TIMESTAMP
        """
    )
    op.execute(
        """
        UPDATE inventory_fornecedor
        SET criado_em = CURRENT_TIMESTAMP
        WHERE criado_em IS NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE inventory_fornecedor
        ALTER COLUMN criado_em DROP DEFAULT
        """
    )
