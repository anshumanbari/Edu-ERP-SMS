# EduCore SMS — Test Suite

Automated tests for the FastAPI backend, introduced in Sprint 18. See
[docs/10_CODING_STANDARDS.md](../docs/10_CODING_STANDARDS.md) for the
project's general code style — it applies to test code too.

## Structure

```
tests/
  conftest.py          # test-DB provisioning, db_session + client fixtures
  pytest.ini            # pytest configuration (markers, coverage, paths)
  unit/                 # no database, no HTTP — pure function/schema logic
  integration/          # real (test) database + real FastAPI app via TestClient
  fixtures/             # reusable pytest fixtures (auth users, sample records)
  utils/                # plain helper functions — test-data factories, DB provisioning
```

- **`unit/`** — tests that touch no database and no network: Pydantic schema
  validation, password hashing, JWT encode/decode, RBAC role-check logic
  called as a plain function. Fast, no setup required beyond `pytest`.
- **`integration/`** — tests that go through a real SQLAlchemy session
  against a dedicated test database, and/or the full FastAPI app via
  `TestClient` (real routing, real RBAC, real response envelopes).
- **`fixtures/`** — pytest fixture modules (`admin_user`, `admin_headers`,
  `sample_student`, etc.), loaded into the session via `pytest_plugins` in
  `conftest.py`. Add a new fixture module here, then list it in
  `conftest.py`'s `pytest_plugins`.
- **`utils/`** — plain functions with no pytest dependency: unique
  email/phone generators (`factories.py`), test-database provisioning
  (`db_provisioning.py`).

## Running the tests

Requires the same local Postgres instance the app already uses (Database
Strategy §2) — tests run against a **separate database**, not the one the
dev server uses, so nothing here touches real data.

```bash
# From the project root:
./.venv/Scripts/python.exe -m pytest -c tests/pytest.ini
```

The first run automatically creates the test database (named
`<your DATABASE_NAME>_test`, derived from `.env`) and brings it to the
latest schema via `alembic upgrade head` — the same migration workflow
introduced in Sprint 17, not `Base.metadata.create_all()`. Subsequent runs
reuse the same test database; each individual test runs inside a
transaction that's rolled back afterward, so tests never see each other's
data and the test database never accumulates rows across runs.

Run only one category:

```bash
./.venv/Scripts/python.exe -m pytest -c tests/pytest.ini -m unit
./.venv/Scripts/python.exe -m pytest -c tests/pytest.ini -m integration
```

## Coverage

Every run produces a coverage report automatically (configured in
`pytest.ini` via `.coveragerc` at the project root):

- Terminal summary (`--cov-report=term-missing`) — printed after the test run.
- HTML report at `htmlcov/index.html` — open it in a browser for a
  line-by-line view. Already covered by `.gitignore`.

## Adding tests for a new module

Following the four-file-per-domain convention
([docs/03_FOLDER_STRUCTURE.md](../docs/03_FOLDER_STRUCTURE.md)):

1. Schema validation → `tests/unit/test_<domain>_schema.py`.
2. CRUD behavior → `tests/integration/test_<domain>_crud.py`.
3. Full API + RBAC → `tests/integration/test_<domain>_api.py`.
4. If the new module needs its own sample-record fixture, add it to
   `tests/fixtures/<domain>_fixtures.py` and register the module in
   `conftest.py`'s `pytest_plugins` list.

## CI/CD readiness

This suite is designed to be runnable non-interactively by a CI pipeline
(Automation Strategy §3.5 / §4) once one exists:

- `requirements-test.txt` at the project root pins the test-only
  dependencies (`pytest`, `pytest-cov`, `httpx`) for a reproducible install.
- The test database is provisioned automatically on first run — no manual
  setup step beyond a reachable Postgres instance and a `.env` file.
- `pytest -c tests/pytest.ini` exits non-zero on any failure, the standard
  signal a CI step needs to gate a build.

No CI configuration file is added in this session — Automation Strategy §5
scoped that to a future, explicitly-requested task.
