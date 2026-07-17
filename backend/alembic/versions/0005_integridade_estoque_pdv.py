"""Transferências e constraints de integridade do estoque/PDV.

Revision ID: 0005_integridade_estoque_pdv
Revises: 0004_permissions
"""

import sqlalchemy as sa
from alembic import op


revision = "0005_integridade_estoque_pdv"
down_revision = "0004_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pos_transferenciaestoquelocal",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "produto_local_id",
            sa.BigInteger(),
            sa.ForeignKey("pos_produtolocal.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantidade", sa.Numeric(12, 2), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(12, 4), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("observacao", sa.String(255), nullable=False, server_default=""),
        sa.Column(
            "criado_por_id",
            sa.BigInteger(),
            sa.ForeignKey("auth_user.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantidade > 0", name="ck_transferencia_quantidade_positiva"),
    )
    op.create_index(
        "ix_transferencia_produto_local_data",
        "pos_transferenciaestoquelocal",
        ["produto_local_id", "data"],
    )
    op.create_check_constraint(
        "ck_produtolocal_estoque_nao_negativo",
        "pos_produtolocal",
        "estoque_atual >= 0",
    )
    op.create_check_constraint(
        "ck_local_desconto_valido",
        "pos_localvenda",
        "desconto_maximo_perc >= 0 AND desconto_maximo_perc <= 100",
    )


def downgrade() -> None:
    op.drop_constraint("ck_local_desconto_valido", "pos_localvenda", type_="check")
    op.drop_constraint("ck_produtolocal_estoque_nao_negativo", "pos_produtolocal", type_="check")
    op.drop_index("ix_transferencia_produto_local_data", table_name="pos_transferenciaestoquelocal")
    op.drop_table("pos_transferenciaestoquelocal")
