"""
Provisions the dedicated test database and brings its schema up to date via
the project's real Alembic migrations (see alembic/) — never via
Base.metadata.create_all(), to stay consistent with the Alembic-based
schema workflow adopted in Sprint 17.

This module must only be imported *after* tests/conftest.py has pointed
DATABASE_NAME at the test database (see resolve_test_database_name below),
so that every app.core.config.settings-derived connection already targets
the test database, never the real one.
"""
import subprocess
import sys
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def resolve_test_database_name(env_file: Path) -> str:
    """
    Read DATABASE_NAME directly out of .env (without importing pydantic
    Settings, since Settings must not be constructed until after the
    DATABASE_NAME override below is in place) and derive the dedicated
    test database name from it.
    """
    base_name = "postgres"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip().startswith("DATABASE_NAME="):
                base_name = line.split("=", 1)[1].strip()
                break
    return f"{base_name}_test"


def ensure_test_database_exists() -> None:
    """
    Create the test database if it doesn't already exist. Idempotent —
    safe to call at the start of every test session.
    """
    from app.core.config import settings  # imported lazily, after override

    admin_url = (
        settings.database_url
        .replace("postgresql+psycopg://", "postgresql://")
        .replace(f"/{settings.database_name}", "/postgres")
    )
    conn = psycopg.connect(admin_url, autocommit=True)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (settings.database_name,),
        )
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{settings.database_name}"')
    finally:
        conn.close()


def apply_migrations() -> None:
    """
    Bring the test database's schema up to date via `alembic upgrade head`,
    run as a subprocess so it uses the exact same alembic/env.py the real
    application relies on (see docs/04_DATABASE_STRATEGY.md). The child
    process inherits the current environment, including the DATABASE_NAME
    override already applied by conftest.py.
    """
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "alembic upgrade head failed while provisioning the test database:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
