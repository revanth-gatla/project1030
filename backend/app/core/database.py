"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from app.core.config import get_settings


def normalize_async_database_url(url: str) -> tuple[str, dict]:
    """Normalize database URL for async drivers (asyncpg, aiosqlite).

    Converts 'postgres://' or 'postgresql://' to 'postgresql+asyncpg://',
    and handles query arguments such as sslmode=require for asyncpg.
    """
    engine_kwargs: dict = {"echo": False}

    if "sqlite" in url:
        engine_kwargs["connect_args"] = {"timeout": 60}
        return url, engine_kwargs

    # Normalize dialect prefix
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]

    # Parse URL components and sanitize query parameters for asyncpg
    parsed = urlsplit(url)
    query_params = parse_qs(parsed.query)
    connect_args: dict = {}

    if "sslmode" in query_params:
        sslmode = query_params.pop("sslmode")[0].lower()
        if sslmode in ("require", "verify-ca", "verify-full", "prefer"):
            connect_args["ssl"] = True
        elif sslmode in ("disable", "allow"):
            connect_args["ssl"] = False

    clean_query = urlencode(query_params, doseq=True)
    clean_url = urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        clean_query,
        parsed.fragment,
    ))

    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    })
    if connect_args:
        engine_kwargs["connect_args"] = connect_args

    return clean_url, engine_kwargs


db_url, engine_kwargs = normalize_async_database_url(get_settings().database_url)
engine = create_async_engine(db_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def migrate_sqlite_schema() -> None:
    """Ensure SQLite tables have updated check constraints and schema columns."""
    import os
    import re
    import sqlite3

    db_path = "medlens.db"
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    try:
        c = conn.cursor()
        c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='lab_results'")
        row = c.fetchone()
        if row:
            sql = row[0]
            if "'LOW'" not in sql or "'HIGH'" not in sql:
                new_sql = re.sub(
                    r"CONSTRAINT\s+\w+\s+CHECK\s*\(\s*reference_status\s+IN\s*\([^)]+\)\s*\)",
                    "CONSTRAINT reference_status_enum CHECK (reference_status IN ('BELOW', 'WITHIN', 'ABOVE', 'UNKNOWN', 'LOW', 'HIGH'))",
                    sql,
                    flags=re.IGNORECASE,
                )
                c.execute("PRAGMA foreign_keys=OFF")
                c.execute("BEGIN TRANSACTION")
                c.execute("ALTER TABLE lab_results RENAME TO _lab_results_old")
                c.execute(new_sql)
                c.execute("INSERT INTO lab_results SELECT * FROM _lab_results_old")
                c.execute("DROP TABLE _lab_results_old")
                conn.commit()
                c.execute("PRAGMA foreign_keys=ON")

        # Migrate clarification_questions columns if missing
        c.execute("PRAGMA table_info(clarification_questions)")
        cq_cols = {col[1] for col in c.fetchall()}
        if cq_cols:
            if "category" not in cq_cols:
                c.execute("ALTER TABLE clarification_questions ADD COLUMN category VARCHAR(100)")
            if "answer" not in cq_cols:
                c.execute("ALTER TABLE clarification_questions ADD COLUMN answer TEXT")
            if "answered_by" not in cq_cols:
                c.execute("ALTER TABLE clarification_questions ADD COLUMN answered_by INTEGER")
            if "answered_at" not in cq_cols:
                c.execute("ALTER TABLE clarification_questions ADD COLUMN answered_at DATETIME")
            conn.commit()
    finally:
        conn.close()
