"""add_volunteers

Revision ID: 0010_add_volunteers
Revises: b478ed433597
Create Date: 2026-07-17

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0010_add_volunteers'
down_revision: Union[str, None] = 'b478ed433597'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'core_voluntario',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('igreja', sa.String(length=255), server_default='', nullable=False),
        sa.Column('area', sa.String(length=255), server_default='', nullable=False),
        sa.Column('regiao', sa.String(length=255), server_default='', nullable=False),
        sa.Column('especialidade', sa.String(length=255), server_default='', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('core_voluntario')
