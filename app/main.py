from fastapi import FastAPI

from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.logger import setup_logging
from app.core.middleware import RequestLoggingMiddleware, StandardResponseMiddleware

# Configure application-wide logging before anything else runs
setup_logging()

# Central API router — aggregates every domain router (see app/routers/__init__.py)
from app.routers import api_router

# Schema is managed by Alembic migrations (see alembic/), not created here —
# run `alembic upgrade head` before starting the app. See docs/04_DATABASE_STRATEGY.md.

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Student Management System — Backend API built with FastAPI",
)

# ---------------------------------------------------------------------------
# Register centralized exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Wrap successful responses in the standard API response envelope
# ---------------------------------------------------------------------------
app.add_middleware(StandardResponseMiddleware)

# ---------------------------------------------------------------------------
# Log every request's method, path, status code, and duration
# ---------------------------------------------------------------------------
app.add_middleware(RequestLoggingMiddleware)

# ---------------------------------------------------------------------------
# Register the central API router (all domain routers included within it)
# ---------------------------------------------------------------------------
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Root health-check endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def health_check():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "status": "Running Successfully",
    }