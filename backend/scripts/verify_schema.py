"""
Verifica compatibilidade entre o schema Django existente e os models SQLAlchemy.

Uso:
  cd backend
  python -m scripts.verify_schema postgresql+asyncpg://user:pass@host:5432/dbname
"""
import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine

EXPECTED_TABLES = {
    # core
    "auth_user",
    "auth_group",
    "auth_user_groups",
    "core_evento",
    "core_centrocusto",
    "core_auditlog",
    "core_configuracaosistema",
    # finance
    "finance_categoriafinanceira",
    "finance_contacaixa",
    "finance_lancamentofinanceiro",
    "finance_anexolancamento",
    # inventory
    "inventory_produto",
    "inventory_entradaestoque",
    "inventory_movimentoestoque",
    "inventory_requisicaosaida",
    "inventory_requisicaosaidaitem",
    "inventory_requisicaosaidaimpressao",
    "inventory_fornecedor",
    "inventory_cotacaocompra",
    "inventory_cotacaocompraitem",
    "inventory_cotacomprecpreco",
    "inventory_cotacaocompraimpressao",
    "inventory_ordemcompra",
    # lodging
    "lodging_chale",
    "lodging_reservachale",
    "lodging_acaochale",
}

COLUMN_OVERRIDES = {
    # (table, column) -> expected PG type substring
    # arquivo: Django usa varchar(100), SQLAlchemy usa varchar(500)
    ("finance_anexolancamento", "arquivo"): "character varying(500)",
    # integer checks: Django adiciona CHECK >= 0, SQLAlchemy não
    ("core_evento", "prev_participantes"): "integer",
    ("core_evento", "prev_trabalhadores"): "integer",
    ("lodging_chale", "capacidade"): "integer",
}


async def verify(dsn: str) -> list[str]:
    engine = create_async_engine(dsn, pool_pre_ping=True)
    errors: list[str] = []

    async with engine.connect() as conn:
        # 1. Listar tabelas existentes
        result = await conn.execute(
            text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' ORDER BY table_name
            """)
        )
        existing = {row[0] for row in result.fetchall()}

        # 2. Verificar tabelas esperadas
        missing = EXPECTED_TABLES - existing
        extra = existing - EXPECTED_TABLES - {
            "django_migrations", "django_content_type",
            "django_session", "auth_permission",
            "auth_user_user_permissions", "auth_group_permissions",
            "notifications_reminderconfig",
            "pos_localvenda", "pos_familiavenda", "pos_produtolocal",
            "pos_entradaestquelocal", "pos_vendamobile",
            "pos_pagamentovenda", "pos_itemvendamobile",
        }

        if missing:
            errors.append(f"❌ TABELAS FALTANDO: {sorted(missing)}")
        if extra:
            errors.append(f"⚠️  TABELAS EXTRAS (Django-only): {sorted(extra)}")

        print(f"✅ Tabelas encontradas: {len(existing & EXPECTED_TABLES)}/{len(EXPECTED_TABLES)}")

        # 3. Verificar colunas de tabelas críticas
        critical_columns = {
            "auth_user": ["id", "username", "email", "password", "is_active", "is_superuser", "is_staff", "last_login", "date_joined"],
            "core_evento": ["id", "nome", "data_inicio", "data_fim", "status", "taxa_base"],
            "finance_lancamentofinanceiro": ["id", "evento_id", "tipo", "categoria_id", "conta_id", "data", "valor", "forma_pagamento", "criado_por_id"],
            "inventory_produto": ["id", "sku", "nome", "estoque_atual", "custo_medio_atual", "ativo"],
            "lodging_reservachale": ["id", "chale_id", "data_entrada", "data_saida", "qtd_pessoas", "status", "pago"],
        }

        for table, expected_cols in critical_columns.items():
            if table not in existing:
                continue
            result = await conn.execute(
                text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = :t AND table_schema = 'public'
                    ORDER BY ordinal_position
                """),
                {"t": table},
            )
            actual = {row[0]: (row[1], row[2]) for row in result.fetchall()}
            for col in expected_cols:
                if col not in actual:
                    errors.append(f"❌ {table}.{col} NÃO EXISTE")

        # 4. Verificar constraints UNIQUE
        result = await conn.execute(
            text("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'UNIQUE' AND tc.table_schema = 'public'
                ORDER BY tc.table_name, kcu.ordinal_position
            """)
        )
        uniques: dict[str, list[str]] = {}
        for row in result.fetchall():
            uniques.setdefault(row[0], []).append(row[1])

        expected_uniques = {
            "auth_user": ["username"],
            "inventory_produto": ["sku"],
            "inventory_requisicaosaida": ["numero"],
            "inventory_cotacaocompra": ["numero"],
            "inventory_ordemcompra": ["cotacao_id"],
            "lodging_chale": ["codigo"],
        }
        for table, cols in expected_uniques.items():
            if table not in uniques:
                continue
            for col in cols:
                if col not in uniques[table]:
                    errors.append(f"⚠️  {table}.{col} deveria ser UNIQUE")

        # 5. Verificar PK types (BigAutoField vs AutoField)
        result = await conn.execute(
            text("""
                SELECT c.table_name, c.column_name, c.data_type
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.columns c
                    ON c.table_name = kcu.table_name
                    AND c.column_name = kcu.column_name
                    AND c.table_schema = 'public'
                WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
            """)
        )
        for row in result.fetchall():
            table, col, dtype = row
            if col == "id" and dtype == "integer" and table in EXPECTED_TABLES:
                errors.append(f"ℹ️  {table}.id é integer (AutoField Django) — OK, compatível")

        # 6. Verificar tipo de coluna arquivo
        result = await conn.execute(
            text("""
                SELECT column_name, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'finance_anexolancamento' AND column_name = 'arquivo'
            """)
        )
        row = result.fetchone()
        if row:
            maxlen = row[1]
            if maxlen and maxlen < 500:
                errors.append(f"⚠️  finance_anexolancamento.arquivo maxLength={maxlen} (Django default=100, SQLAlchemy espera 500). Dados com path>100 chars não existem no Django.")
            else:
                print(f"✅ finance_anexolancamento.arquivo maxLength={maxlen}")

        # 7. Verificar sequences (BigAutoField)
        result = await conn.execute(
            text("""
                SELECT Sequences.sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """)
        )
        print(f"✅ Sequences encontradas: {[r[0] for r in result.fetchall()]}")

    await engine.dispose()
    return errors


async def main():
    if len(sys.argv) < 2:
        print("Uso: python verify_schema.py postgresql+asyncpg://user:pass@host:5432/dbname")
        sys.exit(1)

    dsn = sys.argv[1]
    print(f"🔍 Conectando ao banco Django: {dsn.split('@')[-1] if '@' in dsn else dsn}\n")

    errors = await verify(dsn)

    if errors:
        print("\n" + "=" * 60)
        print("RESULTADO DA VERIFICAÇÃO:")
        print("=" * 60)
        for e in errors:
            print(f"  {e}")
        print(f"\n❌ {len(errors)} problema(s) encontrado(s)")
        sys.exit(1)
    else:
        print("\n✅ Schema 100% compatível — pronto para rodar o FastAPI sobre o banco Django")


if __name__ == "__main__":
    asyncio.run(main())
