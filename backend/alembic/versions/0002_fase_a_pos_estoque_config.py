"""Fase A: POS, Estoque e Configuracoes.

Revision ID: 0002_fase_a_pos_estoque_config
Revises: 0001_baseline
Create Date: 2026-07-14 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_fase_a_pos_estoque_config"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Colunas novas em inventory_produto
    # ------------------------------------------------------------------
    op.add_column(
        "inventory_produto",
        sa.Column("perene", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # ------------------------------------------------------------------
    # 2. Colunas novas em pos_localvenda
    # ------------------------------------------------------------------
    op.add_column(
        "pos_localvenda",
        sa.Column("permite_desconto", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "pos_localvenda",
        sa.Column("desconto_maximo_perc", sa.Integer(), server_default=sa.text("100"), nullable=False),
    )
    op.add_column(
        "pos_localvenda",
        sa.Column("permite_pagamento_misto", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column(
        "pos_localvenda",
        sa.Column("is_deposito_interno", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )

    # ------------------------------------------------------------------
    # 3. Coluna nova em inventory_requisicaosaidaitem
    # ------------------------------------------------------------------
    op.add_column(
        "inventory_requisicaosaidaitem",
        sa.Column("local_origem_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_reqitem_local_origem",
        "inventory_requisicaosaidaitem",
        "pos_localvenda",
        ["local_origem_id"],
        ["id"],
    )

    # ------------------------------------------------------------------
    # 4. Coluna nova em core_configuracaosistema
    # ------------------------------------------------------------------
    op.add_column(
        "core_configuracaosistema",
        sa.Column("modulo_pos_ativo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )

    # ------------------------------------------------------------------
    # 5. Tabela core_configuracaoevento
    # ------------------------------------------------------------------
    op.create_table(
        "core_configuracaoevento",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("evento_id", sa.BigInteger(), nullable=False),
        sa.Column("permite_vendas_pos", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("permite_edicao_estoque_pos", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("permite_lancamentos_financeiro", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("data_fechamento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evento_id"], ["core_evento.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evento_id"),
    )

    # ------------------------------------------------------------------
    # 6. Trigger: sincroniza inventory_produto.estoque_atual a partir
    #    da soma dos pos_produtolocal.estoque_atual
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_atualiza_estoque_global()
        RETURNS TRIGGER AS $$
        DECLARE
            v_produto_id bigint;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                v_produto_id := OLD.produto_id;
            ELSE
                v_produto_id := NEW.produto_id;
            END IF;

            UPDATE inventory_produto
            SET estoque_atual = COALESCE((
                SELECT SUM(estoque_atual)
                FROM pos_produtolocal
                WHERE produto_id = v_produto_id
            ), 0)
            WHERE id = v_produto_id;

            IF TG_OP = 'DELETE' THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_atualiza_estoque_global
        AFTER INSERT OR UPDATE OR DELETE ON pos_produtolocal
        FOR EACH ROW
        EXECUTE FUNCTION fn_atualiza_estoque_global();
    """)

    # ------------------------------------------------------------------
    # 7. Seed: Evento "Sistema" + LocalVenda "Depósito Interno"
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO core_evento (
            nome, data_inicio, data_fim, ativo, status, fechado,
            taxa_base, taxa_trabalhador, adicional_chale,
            observacoes
        )
        SELECT '__SISTEMA__', NOW(), NOW(), false, 'ENCERRADO', true,
               0, 0, 0, 'Evento reservado para depósito interno/transversal'
        WHERE NOT EXISTS (
            SELECT 1 FROM core_evento WHERE nome = '__SISTEMA__'
        );
    """)

    op.execute("""
        INSERT INTO pos_localvenda (
            evento_id, nome, ativo,
            modulo_dashboard, modulo_pdv, modulo_vendas, modulo_produtos, modulo_estoque,
            permite_desconto, desconto_maximo_perc, permite_pagamento_misto, is_deposito_interno,
            criado_em
        )
        SELECT e.id, 'Depósito Interno', false,
               false, false, false, false, false,
               false, 0, false, true,
               NOW()
        FROM core_evento e
        WHERE e.nome = '__SISTEMA__'
          AND NOT EXISTS (
              SELECT 1 FROM pos_localvenda l WHERE l.is_deposito_interno = true
          );
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_atualiza_estoque_global ON pos_produtolocal;")
    op.execute("DROP FUNCTION IF EXISTS fn_atualiza_estoque_global();")

    op.drop_table("core_configuracaoevento")

    op.drop_column("core_configuracaosistema", "modulo_pos_ativo")

    op.drop_constraint("fk_reqitem_local_origem", "inventory_requisicaosaidaitem", type_="foreignkey")
    op.drop_column("inventory_requisicaosaidaitem", "local_origem_id")

    op.drop_column("pos_localvenda", "is_deposito_interno")
    op.drop_column("pos_localvenda", "permite_pagamento_misto")
    op.drop_column("pos_localvenda", "desconto_maximo_perc")
    op.drop_column("pos_localvenda", "permite_desconto")

    op.drop_column("inventory_produto", "perene")
