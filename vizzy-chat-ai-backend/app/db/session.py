from collections.abc import AsyncGenerator
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()
logger = logging.getLogger("vizzy_chat.db")

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)

EXPECTED_TABLE_COLUMNS: dict[str, set[str]] = {
    "chat_history": {
        "id",
        "user_id",
        "user_type",
        "message",
        "context",
        "intent",
        "confidence",
        "reasoning",
        "pathway",
        "generated_response",
        "image_prompts",
        "copy_suggestions",
        "next_suggestions",
        "provider",
        "created_at",
    },
    "user_preferences": {
        "user_id",
        "preferences",
        "updated_at",
    },
}


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


def _sqlite_database_path() -> Path | None:
    prefixes = ("sqlite+aiosqlite:///", "sqlite:///")
    for prefix in prefixes:
        if settings.database_url.startswith(prefix):
            return Path(settings.database_url.replace(prefix, "", 1))
    return None


async def _run_inspector(operation: str) -> Any:
    def inner(sync_connection):
        inspector = inspect(sync_connection)
        if operation == "table_names":
            return inspector.get_table_names()
        raise ValueError(f"Unsupported inspector operation: {operation}")

    async with engine.begin() as connection:
        return await connection.run_sync(inner)


async def get_schema_mismatches() -> dict[str, list[str]]:
    def inspect_schema(sync_connection):
        inspector = inspect(sync_connection)
        mismatches: dict[str, list[str]] = {}
        for table_name, expected_columns in EXPECTED_TABLE_COLUMNS.items():
            if not inspector.has_table(table_name):
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            missing_columns = sorted(expected_columns - existing_columns)
            if missing_columns:
                mismatches[table_name] = missing_columns
        return mismatches

    async with engine.begin() as connection:
        return await connection.run_sync(inspect_schema)


async def reset_database() -> None:
    logger.warning("Resetting local database and recreating tables.")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def initialize_database() -> None:
    from app.models import chat, preference  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    mismatches = await get_schema_mismatches()
    if not mismatches:
        return

    if settings.auto_reset_db_on_schema_mismatch and settings.is_development:
        logger.warning("Detected schema mismatch; auto-resetting local database: %s", mismatches)
        await reset_database()
        return

    mismatch_summary = "; ".join(
        f"{table}: missing {', '.join(columns)}" for table, columns in mismatches.items()
    )
    raise RuntimeError(
        "Database schema mismatch detected. "
        f"{mismatch_summary}. "
        "Run `python -m app.db.manage reset --yes` for local development."
    )


async def init_db() -> None:
    await initialize_database()


async def ping_database() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
