"""add_turno_caixa_pos

Revision ID: b478ed433597
Revises: 0008_pos_locais_globais
Create Date: 2026-07-17 01:34:29.333517

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b478ed433597'
down_revision: Union[str, None] = '0008_pos_locais_globais'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Criar tabela pos_turnocaixa
    op.create_table(
        'pos_turnocaixa',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('local_id', sa.BigInteger(), nullable=False),
        sa.Column('evento_id', sa.BigInteger(), nullable=True),
        sa.Column('aberto_em', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fechado_em', sa.DateTime(timezone=True), nullable=True),
        sa.Column('aberto_por_id', sa.BigInteger(), nullable=False),
        sa.Column('fechado_por_id', sa.BigInteger(), nullable=True),
        sa.Column('valor_abertura', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('valor_fechamento', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('fechado', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('relatorio_pdf', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['aberto_por_id'], ['auth_user.id'], ),
        sa.ForeignKeyConstraint(['fechado_por_id'], ['auth_user.id'], ),
        sa.ForeignKeyConstraint(['local_id'], ['pos_localvenda.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['evento_id'], ['core_evento.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Adicionar caixa_atual_turno_id em pos_localvenda
    op.add_column('pos_localvenda', sa.Column('caixa_atual_turno_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_pos_localvenda_caixa_atual_turno', 'pos_localvenda', 'pos_turnocaixa', ['caixa_atual_turno_id'], ['id'], ondelete='SET NULL')

    # 3. Adicionar turno_id em pos_vendamobile
    op.add_column('pos_vendamobile', sa.Column('turno_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key('fk_pos_vendamobile_turno', 'pos_vendamobile', 'pos_turnocaixa', ['turno_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_pos_vendamobile_turno', 'pos_vendamobile', type_='foreignkey')
    op.drop_column('pos_vendamobile', 'turno_id')
    op.drop_constraint('fk_pos_localvenda_caixa_atual_turno', 'pos_localvenda', type_='foreignkey')
    op.drop_column('pos_localvenda', 'caixa_atual_turno_id')
    op.drop_table('pos_turnocaixa')