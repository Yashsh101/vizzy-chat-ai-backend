from collections.abc import Generator
import logging
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()
logger = logging.getLogger("vizzy_chat.db")

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

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


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _sqlite_database_path() -> Path | None:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        return None
    return Path(settings.database_url.replace(prefix, "", 1))


def get_schema_mismatches() -> dict[str, list[str]]:
    inspector = inspect(engine)
    mismatches: dict[str, list[str]] = {}

    for table_name, expected_columns in EXPECTED_TABLE_COLUMNS.items():
        if not inspector.has_table(table_name):
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = sorted(expected_columns - existing_columns)
        if missing_columns:
            mismatches[table_name] = missing_columns

    return mismatches


def reset_database() -> None:
    logger.warning("Resetting local database and recreating tables.")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def initialize_database() -> None:
    from app.models import chat, preference  # noqa: F401

    Base.metadata.create_all(bind=engine)
    mismatches = get_schema_mismatches()
    if not mismatches:
        return

    if settings.auto_reset_db_on_schema_mismatch and settings.app_env.lower() == "development":
        logger.warning("Detected SQLite schema mismatch: %s", mismatches)
        reset_database()
        return

    mismatch_summary = "; ".join(
        f"{table}: missing {', '.join(columns)}" for table, columns in mismatches.items()
    )
    raise RuntimeError(
        "Database schema mismatch detected. "
        f"{mismatch_summary}. "
        "Run `python -m app.db.manage reset --yes` for local development."
    )


def init_db() -> None:
    initialize_database()


def ping_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
