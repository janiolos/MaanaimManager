"""Torna locais de venda globais/perenes.

Revision ID: 0008_pos_locais_globais
Revises: 0007_pos_local_criado_em
Create Date: 2026-07-15
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_pos_locais_globais"
down_revision = "0007_pos_local_criado_em"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # O local de venda deixa de pertencer a um evento. Vendas continuam
    # vinculadas ao evento por pos_vendamobile.evento_id.
    op.execute(
        """
        ALTER TABLE pos_localvenda
        ALTER COLUMN evento_id DROP NOT NULL
        """
    )

    op.execute(
        """
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            FOR constraint_name IN
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
                WHERE rel.relname = 'pos_localvenda'
                  AND con.contype = 'f'
                  AND att.attname = 'evento_id'
            LOOP
                EXECUTE format('ALTER TABLE pos_localvenda DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$;
        """
    )

    op.execute(
        """
        ALTER TABLE pos_localvenda
        ADD CONSTRAINT fk_pos_localvenda_evento_global
        FOREIGN KEY (evento_id) REFERENCES core_evento(id) ON DELETE SET NULL
        """
    )

    op.execute(
        """
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            FOR constraint_name IN
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'pos_localvenda'
                  AND con.contype = 'u'
                  AND (
                    SELECT array_agg(att.attname::text ORDER BY att.attname::text)
                    FROM unnest(con.conkey) AS col(attnum)
                    JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = col.attnum
                  ) = ARRAY['evento_id', 'nome']::text[]
            LOOP
                EXECUTE format('ALTER TABLE pos_localvenda DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$;
        """
    )

    op.execute(
        """
        WITH duplicados AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY lower(trim(nome))
                    ORDER BY is_deposito_interno DESC, id
                ) AS rn
            FROM pos_localvenda
        )
        UPDATE pos_localvenda l
        SET nome = l.nome || ' #' || l.id
        FROM duplicados d
        WHERE l.id = d.id
          AND d.rn > 1
        """
    )

    op.execute(
        """
        UPDATE pos_localvenda
        SET evento_id = NULL
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_localvenda_nome_global_lower
        ON pos_localvenda (lower(trim(nome)))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_pos_localvenda_nome_global_lower")
    op.execute(
        """
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            FOR constraint_name IN
                SELECT con.conname
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
                WHERE rel.relname = 'pos_localvenda'
                  AND con.contype = 'f'
                  AND att.attname = 'evento_id'
            LOOP
                EXECUTE format('ALTER TABLE pos_localvenda DROP CONSTRAINT %I', constraint_name);
            END LOOP;
        END $$;
        """
    )
    op.execute(
        """
        ALTER TABLE pos_localvenda
        ADD CONSTRAINT fk_pos_localvenda_evento_global
        FOREIGN KEY (evento_id) REFERENCES core_evento(id) ON DELETE CASCADE
        """
    )
    op.execute(
        """
        UPDATE pos_localvenda
        SET evento_id = (SELECT id FROM core_evento ORDER BY id LIMIT 1)
        WHERE evento_id IS NULL
        """
    )
    op.execute(
        """
        ALTER TABLE pos_localvenda
        ALTER COLUMN evento_id SET NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE pos_localvenda
        ADD CONSTRAINT uniq_local_evento_nome UNIQUE (evento_id, nome)
        """
    )
