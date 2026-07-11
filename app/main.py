from fastapi import FastAPI

from app.core.config import settings
from app.core.database import Base, engine
from app.core.error_handlers import register_exception_handlers
from app.core.logger import setup_logging
from app.core.middleware import RequestLoggingMiddleware, StandardResponseMiddleware

# Configure application-wide logging before anything else runs
setup_logging()

# Register ORM models so SQLAlchemy can detect and create their tables
from app.models.student import Student  # noqa: F401
from app.models.teacher import Teacher  # noqa: F401
from app.models.user import User  # noqa: F401

# Routers
from app.routers.student import router as student_router
from app.routers.teacher import router as teacher_router
from app.routers.auth import router as auth_router

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

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
# Task 1 — Register the students router
# ---------------------------------------------------------------------------
app.include_router(student_router)

# ---------------------------------------------------------------------------
# Register the teachers router
# ---------------------------------------------------------------------------
app.include_router(teacher_router)

# ---------------------------------------------------------------------------
# Register the authentication router
# ---------------------------------------------------------------------------
app.include_router(auth_router)


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