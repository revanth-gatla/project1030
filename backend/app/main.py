"""MedLens FastAPI application entry point."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import app.models  # noqa: F401
from app.api.analysis import router as analysis_router
from app.api.auth import router as auth_router
from app.api.patients import router as patients_router
from app.api.pdf import router as pdf_router
from app.api.reports import router as reports_router
from app.core.config import get_settings
from app.core.database import Base, async_session_factory, engine
from app.core.errors import AppError

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup/shutdown."""
    logger.info("medlens_starting")
    try:
        # 1. Ensure all tables exist (works across both SQLite and PostgreSQL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            if "sqlite" in settings.database_url:
                await conn.execute(text("PRAGMA journal_mode=WAL;"))
                await conn.execute(text("PRAGMA busy_timeout=60000;"))

        if "sqlite" in settings.database_url:
            from app.core.database import migrate_sqlite_schema
            migrate_sqlite_schema()

        # 2. Cleanup corrupted records if any
        async with async_session_factory() as session:
            from app.services.report_service import cleanup_corrupted_lab_results
            cleaned = await cleanup_corrupted_lab_results(session)
            if cleaned:
                await session.commit()

        # 3. Seed demonstration dataset if no users exist
        async with async_session_factory() as session:
            from sqlalchemy import select
            from app.models.user import User
            res = await session.execute(select(User).limit(1))
            if res.scalar_one_or_none() is None:
                logger.info("seeding_initial_demo_data")
                from app.seed import seed_data
                await seed_data()
    except Exception as exc:
        logger.warning("startup_initialization_warning", error=str(exc))
    yield
    await engine.dispose()
    logger.info("medlens_stopped")


app = FastAPI(
    title="MedLens API",
    description="AI-Powered Medical Report & Patient Intake Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^https?:\/\/.*(vercel\.app|onrender\.com|localhost).*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(reports_router)
app.include_router(analysis_router)
app.include_router(pdf_router)


# ── Error handler ───────────────────────────────────────────
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "app_error",
        code=exc.code,
        message=exc.message,
        request_id=request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    errors = exc.errors()
    email_error = any("email" in err.get("loc", ()) for err in errors)
    if email_error:
        message = "Please enter a valid email address."
    else:
        message = errors[0].get("msg", "Validation failed.") if errors else "Validation failed."
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("unhandled_error", error=str(exc), request_id=request_id)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "request_id": request_id,
            }
        },
    )


# ── Request ID middleware ───────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Health / Readiness ──────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "medlens-api"}


@app.get("/ready")
async def ready():
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected"},
        )
