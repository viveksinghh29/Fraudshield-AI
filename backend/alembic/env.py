"""
Alembic environment script.

Pulls the DB URL from the application's own Settings (so there is a
single source of truth for the connection string) and uses the
synchronous psycopg driver for migrations — Alembic's autogenerate
and offline modes don't need async, and keeping migrations synchronous
avoids a whole class of event-loop headaches.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `app` importable when Alembic is invoked from the backend/ directory
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app import models  # noqa: E402,F401  (import registers all tables on Base.metadata)

config = context.config
settings = get_settings()

# psycopg (v3) uses the same "postgresql+psycopg" dialect name for both sync
# and async connections -- engine_from_config below creates a plain sync
# engine from this URL, which is what Alembic needs.
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
