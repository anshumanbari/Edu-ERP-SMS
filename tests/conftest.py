"""
Root pytest configuration and fixtures shared by every test in the suite.

Import order in this file is deliberate and must not be reordered:
the DATABASE_NAME environment override below MUST run before anything is
imported from `app` (including transitively, via tests/utils or
tests/fixtures modules), because app.core.config.settings is a singleton
constructed at first import. Once that override is in place, every
settings-derived connection in this process — the app's own engine, this
file's engine, and the `alembic upgrade head` subprocess used to build the
schema — all target the same dedicated test database, never the real one.
"""
import os
from pathlib import Path

from tests.utils.db_provisioning import (
    apply_migrations,
    ensure_test_database_exists,
    resolve_test_database_name,
)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.environ["DATABASE_NAME"] = resolve_test_database_name(_PROJECT_ROOT / ".env")

# ---------------------------------------------------------------------------
# Everything below this line may safely import from `app` — the test
# database override above is already in effect.
# ---------------------------------------------------------------------------
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import engine, get_db
from app.main import app

pytest_plugins = [
    "tests.fixtures.auth_fixtures",
    "tests.fixtures.student_fixtures",
]


@pytest.fixture(scope="session", autouse=True)
def _test_database_schema():
    """
    Provisions the dedicated test database and brings it to the latest
    Alembic revision once per test session — never via
    Base.metadata.create_all() (see docs/04_DATABASE_STRATEGY.md,
    docs/09_MICROSERVICE_EVOLUTION.md's sibling Alembic workflow doc).
    """
    ensure_test_database_exists()
    apply_migrations()
    yield


@pytest.fixture()
def db_session():
    """
    Yields a SQLAlchemy session bound to a single connection/transaction
    that is rolled back at the end of every test, so tests never leak data
    into one another regardless of execution order.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """
    A FastAPI TestClient wired to the same rolled-back-per-test session as
    `db_session`, via a dependency override on `get_db` — the real
    dependency-injection seam every router already uses (Product
    Architecture §3), so no application code needs to change for testing.
    """

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
