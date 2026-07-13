# EduCore SMS — Product Architecture

Status: living document. Reflects actual system state as of 2026-07-13, not the incremental build order in `CLAUDE.md`.

## 1. Product Vision

EduCore is a modular Student Management System (SMS) for educational institutions, built as a single deployable FastAPI backend with clearly separated domain modules. The product covers the full academic lifecycle — enrollment, academic structure, attendance, examinations, results, fees, timetabling — behind a role-gated API, with a read-optimized Dashboard layer for aggregated views.

The near-term target is a single-institution deployment. The architecture is intentionally kept modular so that individual domains (Fees, Attendance, Examination, etc.) can later be extracted into independent services without a rewrite, should the product move toward a multi-tenant SaaS model.

## 2. Business Domains

| Domain | Responsibility |
|---|---|
| Identity & Access | Users, authentication (JWT), roles, permissions (RBAC) |
| Academic Structure | Departments, Programs, Academic Sessions, Semesters, Sections, Classrooms, Subjects, Courses |
| People | Students, Teachers, Teacher Assignments |
| Enrollment | Linking Students to Programs/Sections/Semesters |
| Scheduling | Timetable |
| Attendance | Per-session attendance records |
| Examination | Examinations, Exam Marks |
| Results | Computed/aggregated Results per student/exam/semester |
| Fees | Fee Structures, Fee Payments |
| Dashboard / Reporting | Cross-domain read aggregation for summary and per-domain views |
| Platform | Config, DB session management, logging, error handling, middleware, security |

These domains map closely to the current `app/models`, `app/crud`, `app/schemas`, and `app/routers` contents — each domain generally owns one file per layer.

## 3. Module Boundaries

Each business domain is a **module**: it owns its own model(s), schema(s), CRUD functions, and router. Modules do not reach into each other's CRUD or ORM internals directly — cross-domain reads (e.g., Dashboard) go through each domain's existing CRUD functions rather than writing new ad-hoc queries against another domain's tables.

Current module boundaries:

- **Identity & Access**: `auth`, `user`, RBAC (`app/core/rbac.py`, `app/core/roles.py`) — cross-cutting, consumed by every other module via dependencies, not a peer domain.
- **Academic Structure**: `department`, `program`, `academic_session`, `semester`, `section`, `classroom`, `subject`, `course` — foundational reference data other domains depend on.
- **People**: `student`, `teacher`, `teacher_assignment`.
- **Enrollment**: `enrollment` — join between People and Academic Structure.
- **Scheduling**: `timetable`.
- **Attendance**: `attendance`.
- **Examination & Results**: `examination`, `exam_mark`, `result` — kept as separate modules since marks entry and computed results have different write/read patterns and lifecycles.
- **Fees**: `fee_structure`, `fee_payment`.
- **Dashboard**: `app/dashboard/` — the one intentional exception to the "one router per domain" pattern. It is a **read-only aggregation module**: its `services/` call into existing domain CRUD, its `schemas/` define aggregate/summary response shapes, and it has no models or writes of its own. It depends on every other domain module; no domain module depends on it back.

Rule going forward: a module may depend "downward" on Platform and on core reference modules (Academic Structure, Identity & Access), and Dashboard may depend on any module for reads — but domain modules must not depend on Dashboard or on each other's internals for writes.

## 4. High-Level Folder Structure

```
app/
  core/                  # Platform: config, db session, security, rbac, roles,
                          #   logging, error handling, middleware, shared exceptions
  models/<domain>.py      # SQLAlchemy ORM models, one file per domain
  schemas/<domain>.py     # Pydantic v2 request/response models, one file per domain
  crud/<domain>.py        # DB access layer, one file per domain — routers never touch
                          #   the session directly
  routers/<domain>.py     # FastAPI APIRouter per domain — thin, delegates to crud
  routers/__init__.py     # Central router registration
  dashboard/              # Read-only cross-domain aggregation module
    router.py
    schemas/<area>.py     # Aggregate response shapes (students, teachers, fees, ...)
    services/<area>_service.py  # Aggregation logic, calls into domain crud
  main.py                 # App factory, router registration, startup table creation

docs/                     # Architecture and process documentation (this file lives here)
```

This mirrors the existing repository layout exactly — no restructuring is proposed. The one structural pattern worth naming explicitly: **Dashboard breaks the "flat file per domain" convention on purpose**, because it aggregates across domains rather than owning one. Any future cross-cutting read module (e.g., a future Reporting or Analytics module) should follow the Dashboard pattern (own subpackage with `schemas/` + `services/`), not the flat per-domain pattern.

## 5. Shared Components

Components used by multiple domain modules, living in `app/core/`:

- **`config.py`** — `Settings` (pydantic-settings), the single source of env/config values (`database_url`, `SECRET_KEY`, `ALGORITHM`, etc.). All modules read config through this object.
- **`database.py`** — SQLAlchemy engine, `SessionLocal`, `Base`, `get_db()` dependency. All CRUD modules depend on `Base`; all routers depend on `get_db()`.
- **`security.py`** — password hashing, JWT creation/verification. Consumed by `auth` and by RBAC dependencies.
- **`rbac.py` / `roles.py`** — role definitions and permission-checking dependencies, injected into routers that need to restrict access by role.
- **`exceptions.py` / `error_handlers.py`** — shared exception types and FastAPI exception handlers, registered once in `main.py`, used by any module that raises domain errors.
- **`logger.py`** — shared logging configuration.
- **`middleware.py`** — request-level middleware (e.g., request logging, timing) registered once in `main.py`.

Rule: a shared component lives in `app/core/` only if two or more domain modules need it. Domain-specific helpers stay inside that domain's own files.

## 6. Platform Components

Platform components are infrastructure concerns, not business logic:

- **Web framework**: FastAPI, with `app/main.py` as the composition root (app instance, router registration via `app/routers/__init__.py`, middleware/exception-handler registration, startup `Base.metadata.create_all()`).
- **Database**: PostgreSQL via SQLAlchemy ORM (`postgresql+psycopg://`), single database, one schema, no per-tenant isolation today.
- **Auth**: JWT bearer tokens (`app/core/security.py`), stateless — no session store.
- **Authorization**: RBAC enforced via FastAPI dependencies, not middleware — each router declares the roles/permissions it requires.
- **Logging & error handling**: centralized in `app/core/logger.py` and `app/core/error_handlers.py`, wired once in `main.py` rather than per-router.
- **Schema/migrations**: currently `Base.metadata.create_all()` only — no Alembic. This is a known gap, not an architectural decision; schema changes to existing tables require manual `ALTER TABLE`.

## 7. Future Microservice Boundaries

If/when the system moves toward SaaS/multi-tenant or needs independent scaling, the existing module boundaries (Section 3) are the intended service seams. In rough order of extraction likelihood:

1. **Fees** — distinct compliance/audit needs, natural candidate for isolation (payment processing, financial audit trail).
2. **Examination & Results** — bursty load (exam windows), different backup/retention requirements than core records.
3. **Attendance** — high write volume, could benefit from independent scaling.
4. **Dashboard/Reporting** — read-heavy, a natural fit for a separate read-replica-backed service once aggregation queries grow expensive.
5. **Identity & Access** — would become a shared platform service (Auth/RBAC) consumed by all others, likely the *last* to split since everything depends on it.

Academic Structure and People (Student/Teacher) are expected to remain part of a "core" service indefinitely — nearly every other domain depends on them, so splitting them out first would maximize cross-service chatter.

This section is directional, not a commitment — no extraction work is planned until explicitly scoped.

## 8. Architecture Principles

- **Layered, not layered-leaky**: routers never touch the DB session directly; all queries go through `crud`. This is enforced by convention today, not by tooling — keep it that way in review.
- **One module, one concern**: each domain owns its models/schemas/crud/router. Cross-domain logic (Dashboard) is the explicit exception, not a precedent for casual cross-module coupling.
- **Config through `Settings`, never raw env reads** — keeps all modules deployable the same way.
- **Additive schema evolution**: no destructive migrations without an explicit, reviewed `ALTER TABLE` step; `create_all()` is additive-only by design.
- **RBAC at the router boundary**: authorization is declared per-route via dependencies, not inferred from middleware, so each endpoint's access requirements are visible at its definition.
- **Modules are extraction-ready, not extracted**: module boundaries are drawn so a future microservice split (Section 7) doesn't require redrawing them — but nothing is physically separated today (single DB, single process, single deploy).

## 9. Development Principles

(Restating and grounding the existing project rules from `CLAUDE.md` in this architecture.)

- Modify only the files required for the current task — never rewrite completed modules or touch unrelated code.
- Never regenerate the whole project or change the folder structure unless explicitly asked.
- Never implement future roadmap features automatically — wait for the next explicit task.
- New modules follow the existing per-domain four-file pattern (`models/schemas/crud/routers`) unless they are cross-domain aggregation, in which case they follow the Dashboard subpackage pattern.
- New shared logic goes in `app/core/` only when genuinely shared; otherwise it stays local to the owning module.
- This document (and the rest of `docs/`) describes architecture and intent; it is not a substitute for `CLAUDE.md`'s command/verification instructions, which remain the operational source of truth.

## 10. Recommended Documentation Structure

Proposed `docs/` layout for ongoing architecture work (this session creates only file 01; the rest are named here for continuity across sessions):

```
docs/
  01_PRODUCT_ARCHITECTURE.md   # this file — vision, domains, boundaries, principles
  02_DATA_ARCHITECTURE.md      # entity relationships, ERD-level view, data ownership per module
  03_API_ARCHITECTURE.md       # API conventions, versioning stance, pagination/filter/sort pattern
  04_SECURITY_ARCHITECTURE.md  # authN/authZ model, RBAC role matrix, token lifecycle
  05_DEPLOYMENT_ARCHITECTURE.md # environments, config/secrets handling, deployment topology
  06_DECISIONS/                # one ADR (Architecture Decision Record) file per significant decision
```

Only `01_PRODUCT_ARCHITECTURE.md` is created in this session. The others are placeholders for future architecture sessions and should not be created until explicitly scoped.
