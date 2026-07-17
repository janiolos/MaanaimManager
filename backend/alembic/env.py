"""Alembic environment - async SQLAlchemy.

Para criar uma baseline do schema Django atual:
    alembic revision -m "baseline legacy django schema" --autogenerate
e em seguida marcar como aplicada sem rodar:

    alembic stamp head
"""

from __future__ import annotations

import asyncio
import logging.config
from logging import getLogger

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.core import models  # noqa: F401 - garante registro no metadata
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    logging_config = config.config_file_name
    if logging_config.endswith(".ini"):
        logging.config.fileConfig(logging_config)

# override sqlalchemy.url com settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

logger = getLogger("alembic.env")

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=False,
    )
    with context.begin_transaction():
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


run_migrations_online()