# EduCore SMS — Developer Platform

Status: living document. Introduced in Sprint 19. Documents the `scripts/` package — a set of small, single-purpose command-line tools that wrap the project's existing workflows (uvicorn, Alembic, pytest, ruff) behind consistent, scriptable commands. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [07_AUTOMATION_STRATEGY.md](07_AUTOMATION_STRATEGY.md) and the Alembic ([04_DATABASE_STRATEGY.md](04_DATABASE_STRATEGY.md)) and testing (`tests/README.md`) workflows established in Sprints 17–18.

## 1. Purpose

Every script here wraps a command that was already documented somewhere (CLAUDE.md's Commands section, `tests/README.md`, `alembic` usage) — nothing here introduces a new way of doing things, it makes the existing way one command instead of remembering the exact flags. **No script contains business logic** — they call into `app/` the same way a developer would (importing `settings`, running `alembic`/`pytest`/`ruff` as subprocesses), never duplicating what already exists there.

## 2. Invocation Convention

Every script is a package module, run with the project's own venv interpreter using `-m`:

```bash
./.venv/Scripts/python.exe -m scripts.<category>.<script> [options]
```

This matches the project's existing convention (`-m uvicorn`, `-m pytest`, `-m alembic`) and is what makes `scripts/`'s internal imports (`from scripts._shared.common import ...`) resolve correctly without any `sys.path` hacking — `-m` puts the project root on `sys.path` automatically. Running a script by file path directly (`python scripts/development/start.py`) will NOT work.

Every script supports `--help`.

## 3. Folder Structure

```
scripts/
  __init__.py
  _shared/
    __init__.py
    common.py            # subprocess runner, console output, confirm(), PROJECT_ROOT/PYTHON
  development/
    start.py              # run the dev server
    stop.py                # stop whatever's on the dev server's port
    clean.py               # remove caches/coverage artifacts
    reset.py               # rebuild the local database from scratch
    info.py                 # print project/environment snapshot
  database/
    migrate.py             # alembic upgrade
    revision.py            # alembic revision --autogenerate
    rollback.py            # alembic downgrade
    history.py             # alembic history / current
    seed.py                 # baseline admin user + reference data
  quality/
    test.py                 # run the test suite
    coverage.py             # run tests, report coverage location
    lint.py                  # ruff check
    format.py                # ruff format
    security.py              # static checks + pip-audit
  environment/
    check.py                 # verify local prerequisites
    verify.py                 # full health gate (check + import + migrations [+ tests])
```

`scripts/_shared/` is the one addition beyond the requested tree — it exists solely so `run_module()`, `confirm()`, and the console-output helpers have one implementation, per the "do not duplicate logic" requirement. It's not a command category; nothing in it is meant to be run directly.

## 4. Script Responsibilities

### development/
| Script | Responsibility |
|---|---|
| `start.py` | Runs `uvicorn app.main:app --reload` (configurable `--host`/`--port`/`--no-reload`) — the exact command from CLAUDE.md's Commands section. |
| `stop.py` | Finds and kills whatever process is listening on the dev server's port (default 8000). Cross-platform: `netstat`/`taskkill /F /T` on Windows, `lsof`/`kill -9` on POSIX. The `/T` (tree-kill) flag matters — `uvicorn --reload` runs the real server as a child of the reloader process; killing only the parent leaves an orphaned child still holding the port (found and fixed during verification, see §5). |
| `clean.py` | Removes `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `htmlcov/`, `.coverage` — never touches `.venv`, `.git`, or source. |
| `reset.py` | Rebuilds the local database from scratch: `alembic downgrade base` then `alembic upgrade head` (reuses `database.rollback.downgrade`/`database.migrate.upgrade` — no separate alembic invocation logic). Destructive — confirmation required unless `--yes`. Optional `--seed` runs `database.seed` afterward. |
| `info.py` | Prints app name/version, Python/interpreter, OS, database host/port/name (never credentials), current git branch (read-only), and current Alembic revision. |

### database/
| Script | Responsibility |
|---|---|
| `migrate.py` | `alembic upgrade <revision>` (default `head`). Exposes `upgrade()` for reuse by `reset.py`. |
| `revision.py` | `alembic revision --autogenerate -m <message>` (or `--no-autogenerate` for an empty revision). |
| `rollback.py` | `alembic downgrade <revision>` (default `-1`). Destructive — confirmation required unless `--yes`. Exposes `downgrade()` for reuse by `reset.py`. |
| `history.py` | Prints `alembic history --verbose` and `alembic current`. Read-only. |
| `seed.py` | Idempotently seeds a baseline admin user (`--admin-email`/`--admin-password`) plus one Department/AcademicSession/Program, using the app's own `hash_password`/ORM models directly — the same out-of-band pattern real admin provisioning would need, since self-registration can't create an admin (Security Architecture §3). |

### quality/
| Script | Responsibility |
|---|---|
| `test.py` | `pytest -c tests/pytest.ini`, with `--unit`/`--integration` shortcuts and pass-through args. Exposes `run_tests()` for reuse by `coverage.py` and `verify.py`. |
| `coverage.py` | Runs the suite (via `test.run_tests()` — coverage collection is already configured in `tests/pytest.ini`) and reports/optionally opens the `htmlcov/index.html` report. |
| `lint.py` | `ruff check app tests scripts alembic` (config: `pyproject.toml`). `--fix` to auto-fix. |
| `format.py` | `ruff format` on the same paths. `--check` for a CI-friendly dry run. |
| `security.py` | Three static, network-independent checks drawn directly from gaps already recorded in `docs/05_SECURITY_ARCHITECTURE.md`/`docs/04_DATABASE_STRATEGY.md` (`.env` is gitignored, no hardcoded `SECRET_KEY`/`DATABASE_PASSWORD` literals in `app/`, `engine.echo` hardcoding), plus a best-effort `pip-audit` dependency scan (`--skip-audit` to omit; a failed/offline audit warns, it doesn't fail the whole check). |

### environment/
| Script | Responsibility |
|---|---|
| `check.py` | Verifies Python version, active virtualenv, `.env` present with all required keys populated (values never printed), database reachability, and that required packages are importable. Exposes `run_checks()`. |
| `verify.py` | The single CI-ready gate: `check.run_checks()` + `import app.main` sanity check + Alembic current-vs-head comparison, with an optional `--with-tests` to also run the full suite. Exits non-zero on any failure. |

## 5. Verification Summary

Every script was run at least once during this sprint:

- **Safe/read-only** (`environment.check`, `environment.verify`, `development.info`, `development.clean`, `quality.lint`, `quality.format --check`, `quality.security`, `quality.test`, `quality.coverage`, `database.history`, `database.migrate`) — run directly against the real dev environment. All behaved as documented.
- **`development.start` / `development.stop`** — run together against a scratch port (8010/8011). First run surfaced a real bug: `stop.py` killed only the `uvicorn --reload` parent, leaving the child server process alive and still serving. Fixed by adding Windows' `/T` tree-kill flag; re-verified clean stop (connection refused afterward).
- **`database.revision`** — verified by generating a real (empty, `--no-autogenerate`) revision file, confirming it applied Alembic's standard template correctly, then removing the file (it was a verification artifact, not an intended schema change) so `alembic history` still shows a single clean head.
- **`database.rollback` / `development.reset`** — destructive, so verified against a disposable scratch database created and dropped for this purpose only (same pattern used in Sprint 17), never the real dev database. `migrate → rollback --revision base → reset --seed` all completed correctly end-to-end.
- **`database.seed`** — run for real against the dev database (additive/idempotent, safe to keep): created one admin user, one Department, one AcademicSession, one Program; a second run correctly skipped all four as already existing.
- **Encoding issue found and fixed**: several scripts' console messages used an em dash (`—`), which the Windows console's default codepage couldn't render (printed as `�`/mangled). Replaced with plain ASCII across every script for reliable output on any terminal or CI log.
- **Full gate**: `environment.verify --with-tests` passes end-to-end (environment checks, import sanity, migration status, and all 34 tests from Sprint 18's suite).

## 6. Future Extensions

Not built in this sprint, left for an explicitly-scoped future task (per CLAUDE.md's "never implement future roadmap features automatically"):

- **`scripts/development/docker.py`** or an actual `Dockerfile`/`docker-compose.yml` — this sprint made the scripts Docker-ready (no interactive prompts without `--yes`, `sys.executable`-based subprocess invocation that works with whatever Python a container provides, consistent non-zero exit codes) but did not add container definitions themselves, consistent with Deployment Architecture §8 deferring containerization until a hosting target is chosen.
- **CI workflow file** (e.g. `.github/workflows/ci.yml`) wiring `environment.verify --with-tests`, `quality.lint`, and `quality.format --check` into an actual pipeline — Automation Strategy §3.5 already scoped this as a distinct future item; this sprint only made the underlying commands CI-invokable.
- **A full `requirements.txt`** for the application's own runtime dependencies (fastapi, sqlalchemy, psycopg, etc.) — still the pre-existing gap from Automation Strategy §3.1, not addressed here. This sprint added `requirements-dev.txt` (ruff, pip-audit, alembic) and reused Sprint 18's `requirements-test.txt`, scoped strictly to the new tooling this sprint introduces.
- **`scripts/quality/typecheck.py`** (mypy) — mentioned as a future item in Automation Strategy §3.4 but not built here; no mypy configuration exists yet.

## 7. Design Decisions

- **`sys.executable` as the interpreter for every subprocess**, not a hunted-for venv path — since every script is meant to be invoked with the project's own venv Python (`-m scripts...`), `sys.executable` already *is* that interpreter, and this makes every script work unmodified inside a future Docker image or CI runner regardless of where the venv lives.
- **`scripts/_shared/common.py` added beyond the requested tree** — the explicit "do not duplicate logic" requirement isn't satisfiable with four independent folders and no shared code; this is the minimum addition to satisfy it, not a new command category.
- **Destructive operations (`rollback`, `reset`) require `--yes`/`-y` to skip an interactive confirmation** — safe by default for a human running it locally, but CI/Docker-invokable without hanging on stdin when the flag is passed.
- **`seed.py` inserts the admin user directly via the ORM, not through `crud.create_user`** — identical reasoning to Sprint 18's test fixtures: `UserCreate.role` intentionally excludes `admin` from self-registration, so provisioning the first admin has to happen out-of-band by design, and this script is that out-of-band path for local dev.
- **`security.py`'s static checks are narrow and reuse findings already on record** (Security/Database Strategy docs), rather than inventing a broad new rule set — keeps the check fast, dependency-free, and free of false positives, with `pip-audit` as the one part that needs network and is allowed to degrade to a warning rather than block local development.
- **All console output converted to plain ASCII** after the em-dash rendering bug was found on Windows — correctness here was verified empirically, not assumed, and the fix applies uniformly rather than per-script.
- **No Dockerfile, CI workflow, or full application `requirements.txt` added** — each is a distinct, larger decision (hosting target, CI provider, full dependency pinning) already deferred by name in Deployment Architecture and Automation Strategy; this sprint's job was making the underlying commands ready for those, not making those decisions.
