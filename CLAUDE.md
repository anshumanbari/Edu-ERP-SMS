# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

EduCore Backend — a FastAPI-based Student Management System (SMS). Currently implements the Student module end-to-end; more modules (Teacher, Auth, RBAC, Dashboard, Attendance, Course) are planned incrementally — see "Roadmap" below.

## Commands

There is no `requirements.txt`/`pyproject.toml` yet — dependencies live only in `.venv`. Use the venv's Python/uvicorn directly:

```bash
# Run the dev server (auto-reload)
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

# Quick import/sanity check (also creates missing tables via Base.metadata.create_all)
./.venv/Scripts/python.exe -c "import app.main; print('IMPORT OK')"
```

There is no test suite or linter configured. Verification is done by running the server and hitting endpoints with `curl` (see examples for each router in `app/routers/`), or via the interactive docs at `http://127.0.0.1:8000/docs`.

Schema changes to existing tables require a manual `ALTER TABLE` — there is no Alembic/migrations setup. `Base.metadata.create_all()` (called on startup in `app/main.py`) only creates tables that don't exist yet; it never alters existing columns.

## Architecture

Layered structure, one sub-package per concern, mirrored per domain module (currently only `student`):

```
app/
  core/
    config.py      # pydantic-settings Settings, loads .env, exposes settings.database_url
    database.py    # SQLAlchemy engine/session, Base, get_db() dependency
  models/<domain>.py    # SQLAlchemy ORM models (declarative, Mapped[] style)
  schemas/<domain>.py   # Pydantic v2 request/response models
  crud/<domain>.py      # All DB queries live here — routers never touch the session directly
  routers/<domain>.py   # FastAPI APIRouter — thin: validates via Depends(get_db), delegates to crud, raises HTTPException
  main.py          # Creates FastAPI app, registers routers, runs Base.metadata.create_all()
```

Request flow: `router` → `crud` (via `Depends(get_db)` session) → SQLAlchemy `Student` model → Postgres. Response shaping happens via Pydantic `response_model` on each route (`StudentResponse`, `PaginatedStudentResponse`, `StudentDeleteResponse` in `app/schemas/student.py`).

### Config

`app/core/config.py` defines a `Settings(BaseSettings)` reading from `.env` (`DATABASE_HOST/PORT/NAME/USER/PASSWORD`, `SECRET_KEY`, `ALGORITHM`, etc.). `settings.database_url` builds a `postgresql+psycopg://` URL. All new domain modules should read config through this same `settings` object rather than reading env vars directly.

### GET /students — combined query pattern

The list endpoint (`app/routers/student.py` `get_all_students` + `app/crud/student.py` `get_paginated_students`) is the reference pattern for any future paginated/filterable/sortable list endpoint:

- **Pagination**: `page` (default 1), `limit` (default 10, max 100) → `offset = (page - 1) * limit`.
- **Search**: `search` param does an `OR`'d `ILIKE` across `name`, `email`, and `cast(phone, String)` (phone is `BigInteger`, so it's cast to text for substring matching).
- **Filtering**: `course` (exact match), `semester` (exact match) — applied as additional `.filter()` calls before the count/pagination.
- **Sorting**: `sort_by: Literal["id", "name", "semester"]`, `sort_order: Literal["asc", "desc"]` (default `"asc"`) — resolved via `getattr(Student, sort_by)` and applied *after* computing `total_records` but before `.offset().limit()`.
- Filters/search/sort all compose in a single SQLAlchemy query built incrementally in `get_paginated_students`; `total_records` is counted after filters but the row fetch also gets `.offset()/.limit()` applied afterward.

### Notable model decisions

- `Student.phone` is `BigInteger` (not `String`) — an intentional choice per explicit project requirement, despite the general best practice of storing phone numbers as strings (loses leading zeros / `+` country codes). `StudentBase.phone` schema field is validated as `int` with `ge=1000000, le=999999999999999` (7–15 digits).
- `Student.email` has a DB-level `unique=True` constraint; `crud.create_student` also does an explicit pre-check query and raises `409 Conflict` before insert (belt-and-suspenders, not relying on the DB constraint error alone).
- DELETE returns `200 OK` with a `StudentDeleteResponse {"message": ...}` body, not a bare `204 No Content`.

## Coding Rules (from project owner)

- Follow FastAPI best practices; use SQLAlchemy ORM; use Pydantic v2; use type hints.
- Modify only the files required for the current task — never rewrite completed modules or touch unrelated code.
- Never regenerate the whole project or change the folder structure unless explicitly asked.
- Never implement future roadmap features automatically — wait for the next explicit task.

## Roadmap (do not build ahead of the current task)

Completed: Project setup, PostgreSQL connection, Student model/schema/CRUD, pagination, search, filtering, sorting.

Next: Teacher module, then JWT Authentication, RBAC, Dashboard, Attendance, Course, SaaS refactoring — in that order, one at a time.
