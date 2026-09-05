"""Test database URL normalization for cloud deployment (e.g. Render PostgreSQL)."""

from app.core.database import normalize_async_database_url


def test_sqlite_url_preserved():
    url, kwargs = normalize_async_database_url("sqlite+aiosqlite:///./medlens.db")
    assert url == "sqlite+aiosqlite:///./medlens.db"
    assert "timeout" in kwargs["connect_args"]


def test_postgres_render_url_converted_to_asyncpg():
    raw_url = "postgres://medlens_user:secret_pass@dpg-abc123-a.oregon-postgres.render.com/medlens_db"
    clean_url, kwargs = normalize_async_database_url(raw_url)
    assert clean_url.startswith("postgresql+asyncpg://")
    assert "medlens_user:secret_pass" in clean_url
    assert kwargs.get("pool_pre_ping") is True


def test_postgresql_with_sslmode_require_sanitized_for_asyncpg():
    raw_url = "postgresql://user:pass@ep-cool-123.render.com:5432/medlens?sslmode=require"
    clean_url, kwargs = normalize_async_database_url(raw_url)
    assert clean_url.startswith("postgresql+asyncpg://")
    # sslmode should not remain in query string (causes asyncpg TypeError)
    assert "sslmode" not in clean_url
    # ssl should be configured in connect_args
    assert kwargs.get("connect_args", {}).get("ssl") is True


def test_postgresql_asyncpg_already_specified():
    raw_url = "postgresql+asyncpg://medlens:medlens@localhost:5432/medlens"
    clean_url, kwargs = normalize_async_database_url(raw_url)
    assert clean_url == raw_url
    assert kwargs.get("pool_pre_ping") is True
