import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from dotenv import load_dotenv

# Only load .env in local dev, not in Docker
if not os.getenv("DOCKER_ENV"):
    load_dotenv()

# Import your base and all models so alembic can see them
from database import Base
from models.schemas import (
    APIKey,
    Document,
    ExtractionJob,
    ExtractionResult,
    UsageLog,
)

# Alembic config object
config = context.config

# Override sqlalchemy.url with value from environment if available
db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

# asyncpd URL for the engine
config.set_main_option("sqlalchemy.url", db_url)

# set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
    
# This is what Alembic uses to detect schema changes
target_metadata = Base.metadata


def run_migration_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
        
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()
        
async def run_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migration_online() -> None:
    asyncio.run(run_migrations())
    

if context.is_offline_mode():
    run_migration_offline()
else:
    run_migration_online()
    
    