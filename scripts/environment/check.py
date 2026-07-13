"""
Verify local prerequisites are in place: Python version, an active
virtualenv, a populated .env file, a reachable Postgres instance, and the
key third-party packages the project depends on. Never prints credential
values - only presence/reachability.

Usage:
    python -m scripts.environment.check
"""
import argparse
import sys

from scripts._shared.common import PROJECT_ROOT, fail, ok, warn

REQUIRED_ENV_KEYS = [
    "APP_NAME", "APP_VERSION",
    "DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD",
    "SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
]

REQUIRED_PACKAGES = ["fastapi", "sqlalchemy", "pydantic", "psycopg", "alembic", "pytest", "ruff"]


def _check_python_version() -> bool:
    if sys.version_info >= (3, 10):
        ok(f"Python {sys.version.split()[0]} (>= 3.10 required for PEP 604 union types used in app/models).")
        return True
    fail(f"Python {sys.version.split()[0]} is too old - this project requires Python 3.10+.")
    return False


def _check_virtualenv_active() -> bool:
    if sys.prefix != sys.base_prefix:
        ok(f"Running inside a virtual environment ({sys.prefix}).")
        return True
    warn("Not running inside a virtual environment - expected `.venv`'s interpreter.")
    return False


def _check_env_file() -> bool:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        fail(".env not found at project root.")
        return False

    present_keys = set()
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if value.strip():
            present_keys.add(key.strip())

    missing = [key for key in REQUIRED_ENV_KEYS if key not in present_keys]
    if missing:
        fail(f".env is missing or has empty values for: {', '.join(missing)}")
        return False
    ok(".env is present with all required keys populated.")
    return True


def _check_database_reachable() -> bool:
    try:
        import psycopg

        from app.core.config import settings

        url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
        conn = psycopg.connect(url, connect_timeout=3)
        conn.close()
        ok(
            f"Database '{settings.database_name}' reachable at "
            f"{settings.database_host}:{settings.database_port}"
        )
        return True
    except Exception as exc:  # noqa: BLE001 - any connection failure means "not reachable"
        fail(f"Database is not reachable: {type(exc).__name__}")
        return False


def _check_dependencies_importable() -> bool:
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        fail(f"Missing required packages: {', '.join(missing)}")
        return False
    ok("All required packages are importable.")
    return True


def run_checks() -> bool:
    results = [
        _check_python_version(),
        _check_virtualenv_active(),
        _check_dependencies_importable(),
        _check_env_file(),
        _check_database_reachable(),
    ]
    return all(results)


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(
        description="Check that local prerequisites (Python, venv, .env, database) are in place."
    ).parse_args(argv)
    return 0 if run_checks() else 1


if __name__ == "__main__":
    sys.exit(main())
