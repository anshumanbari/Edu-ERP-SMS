# EduCore SMS — Folder Structure

Status: living document. Reflects the actual repository layout as of 2026-07-13, including the in-progress central router registration refactor. Documentation only — no code, APIs, or DB schema created or changed by this session. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) and [02_DOMAIN_ARCHITECTURE.md](02_DOMAIN_ARCHITECTURE.md).

## 1. Purpose

Product Architecture §4 gave the folder structure at a glance. This document is the detailed reference: what goes in each directory, the naming/file-per-domain convention, the current registration pattern for models and routers, and the rules for adding a new module without breaking the convention.

## 2. Full Repository Layout

```
Students-SMS/
  app/
    __init__.py
    main.py                         # App factory: FastAPI instance, middleware,
                                     #   exception handlers, model imports (for
                                     #   create_all), single api_router include
    core/                           # Platform layer — shared by every domain module
      config.py                     # Settings (pydantic-settings)
      database.py                   # engine, SessionLocal, Base, get_db()
      security.py                   # password hashing, JWT
      rbac.py                       # permission-checking dependencies
      roles.py                      # Role enum / role definitions
      exceptions.py                 # shared exception types
      error_handlers.py             # FastAPI exception handler registration
      logger.py                     # logging setup
      middleware.py                 # RequestLoggingMiddleware, StandardResponseMiddleware
    models/<domain>.py               # SQLAlchemy ORM models — one file per domain entity
    schemas/<domain>.py              # Pydantic v2 schemas — one file per domain entity
    crud/<domain>.py                 # DB access functions — one file per domain entity
    routers/
      __init__.py                   # Central registration: imports every domain router,
                                     #   mounts them onto one `api_router = APIRouter()`
      <domain>.py                   # FastAPI APIRouter per domain — one file per domain entity
    dashboard/                      # Read-only cross-domain aggregation module (exception
                                     #   to the flat per-domain layout — see §4)
      __init__.py
      router.py
      schemas/<area>.py
      services/<area>_service.py
  docs/                             # Architecture documentation (this file's directory)
    01_PRODUCT_ARCHITECTURE.md
    02_DOMAIN_ARCHITECTURE.md
    03_FOLDER_STRUCTURE.md          # this file
  .venv/                            # Virtual environment (dependencies live only here —
                                     #   no requirements.txt/pyproject.toml yet)
  .env                              # DATABASE_HOST/PORT/NAME/USER/PASSWORD, SECRET_KEY, ALGORITHM
```

## 3. The Four-File-Per-Domain Convention

Every domain entity in Section 2/3 of the Domain Architecture (Student, Teacher, Department, Program, Semester, Section, Course, Subject, Classroom, AcademicSession, Enrollment, TeacherAssignment, Timetable, Attendance, Examination, ExamMark, Result, FeeStructure, FeePayment, User) follows the same four-file pattern, one file per layer, same base filename across all four:

```
app/models/<domain>.py     → ORM model
app/schemas/<domain>.py    → Pydantic request/response models
app/crud/<domain>.py       → query functions, called only by that domain's router
app/routers/<domain>.py    → APIRouter, delegates to crud, never touches the session directly
```

`auth.py` is the one router without a matching `models/crud` pair of its own — it operates on the `User` model/schema/crud (Identity & Access, per Domain Architecture §3.1) rather than owning a separate entity.

## 4. The Dashboard Exception

`app/dashboard/` intentionally does not follow the flat four-file convention, because it isn't a domain — it's a read-only aggregator over multiple domains (Product Architecture §3, Domain Architecture §3.9):

```
app/dashboard/
  router.py                 # single router, multiple aggregate endpoints
  schemas/<area>.py          # one file per aggregate *area*, not per entity
                             #   (students, teachers, attendance, examination, fees, academic, summary, system)
  services/<area>_service.py # aggregation logic; calls into existing domain crud
                             #   modules, never queries another domain's table directly
                             #   and never writes
```

This is the sanctioned template for any future cross-domain read module (e.g., a future Reporting/Analytics module) — own subpackage, `schemas/` + `services/` split by *area* rather than *entity*, no `models/` or `crud/` of its own.

## 5. Router Registration Pattern (current refactor)

The repository is mid-refactor (branch `refactor/central-router-registration`) consolidating router registration into one place:

- **`app/routers/__init__.py`** imports every domain router module and mounts each onto a single `api_router = APIRouter()` via `api_router.include_router(...)`. This includes `app.dashboard.router` alongside the domain routers, even though `dashboard/` lives outside `app/routers/`.
- **`app/main.py`** imports only `api_router` from `app.routers` and calls `app.include_router(api_router)` once — it no longer imports or registers individual domain routers directly.
- **Model imports in `main.py`**: every model is still imported individually in `main.py` (with `# noqa: F401`) purely so `Base.metadata.create_all()` at startup sees every table. This is a side-effect-only import list, separate from and unaffected by the router consolidation.

Convention going forward: a new domain module's router is registered by adding one import + one `include_router` line to `app/routers/__init__.py` — `main.py` itself should not need to change when a new domain module is added, only when a new *model* needs to be picked up by `create_all()`.

## 6. Adding a New Domain Module — Checklist

For a new module following the standard (non-Dashboard) pattern:

1. `app/models/<domain>.py` — ORM model; add its import to `app/main.py`'s model-import block (for `create_all()`).
2. `app/schemas/<domain>.py` — Pydantic v2 schemas.
3. `app/crud/<domain>.py` — query functions; routers never touch the DB session directly.
4. `app/routers/<domain>.py` — APIRouter; register it in `app/routers/__init__.py` (import + `include_router`).
5. If the module needs shared logic used by ≥2 domains, it goes in `app/core/`, not duplicated per-module (Product Architecture §5).

For a new *cross-domain read* module, follow §4's Dashboard template instead of this checklist.

## 7. What Does Not Live Under `app/`

- **`docs/`** — architecture and process documentation (this session's output), not consumed by the running application.
- **`.venv/`** — dependencies; no `requirements.txt`/`pyproject.toml` exists yet (noted in CLAUDE.md as a known gap, not addressed here).
- **`.env`** — environment configuration consumed via `app/core/config.py`'s `Settings`; never read directly by any other module (Product Architecture §5).

No changes to this layout are proposed in this session — it documents the structure as it stands, including the in-flight router-registration refactor.
