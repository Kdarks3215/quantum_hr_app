﻿from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import create_app, db
from app.models import *  # noqa: F401,F403

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ensure DATABASE_URL from environment overrides alembic.ini default
if os.environ.get("DATABASE_URL"):
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

app = create_app({"SQLALCHEMY_DATABASE_URI": config.get_main_option("sqlalchemy.url"), "SEED_DEFAULT_DATA": False})

target_metadata = db.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
