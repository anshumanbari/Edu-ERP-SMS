# EduCore SMS — Database Strategy

Status: living document. Reflects the actual database setup as of 2026-07-13. Documentation only — no code, APIs, or DB schema created or changed by this session. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) and [02_DOMAIN_ARCHITECTURE.md](02_DOMAIN_ARCHITECTURE.md).

## 1. Purpose

Product Architecture §6 named schema/migrations as a platform component with a known gap (no Alembic). This document is the detailed database strategy: engine/connection setup, schema lifecycle, ID/typing/constraint conventions actually in use, indexing strategy, and the migration approach for when `create_all()` stops being sufficient.

## 2. Engine & Connection

- **Database**: PostgreSQL, single instance, single schema, single database — no per-tenant isolation (consistent with Product Architecture §6).
- **Driver**: `psycopg` (v3) via SQLAlchemy's `postgresql+psycopg://` dialect.
- **Connection URL**: built exclusively by `Settings.database_url` (`app/core/config.py`) from `DATABASE_HOST/PORT/NAME/USER/PASSWORD` env vars — no module should construct a connection string itself.
- **Session management**: `app/core/database.py` — one `engine`, one `SessionLocal` (`autocommit=False, autoflush=False`), one `Base` (`DeclarativeBase`), and `get_db()` as the single FastAPI dependency every router uses to obtain a session. A request gets exactly one session for its lifetime, closed in `finally`.
- **`echo=True`** is currently set on the engine — all SQL is logged. This is a development-time setting; it is not gated by an environment flag today (noted as a gap, see §8).

## 3. Schema Lifecycle

- **Creation**: `Base.metadata.create_all(bind=engine)`, called once at app startup in `app/main.py`. It only creates tables that don't already exist — it never alters existing columns, drops columns, or adds constraints to existing tables.
- **Model registration for `create_all()`**: every model must be imported somewhere before `create_all()` runs, which is why `main.py` has an explicit (and slightly redundant-looking) block of `from app.models.<x> import <X>  # noqa: F401` for every domain entity. This import list is a startup side-effect mechanism, not a router-registration concern (see Folder Structure §5) — a new model that isn't imported here silently never gets a table.
- **Alteration**: manual `ALTER TABLE`, executed directly against Postgres. There is no tracked history of these changes and no tool enforcing that they've been applied consistently across environments. This is the single biggest schema-lifecycle risk in the current setup (see §8).
- **No Alembic** (or other migration tool) is configured. This is a deliberate, acknowledged gap per CLAUDE.md, not an oversight to silently work around.

## 4. Primary Key & ID Strategy

- Every table uses a single-column surrogate primary key: `id: Mapped[int] = mapped_column(primary_key=True, index=True)`, Postgres-native auto-incrementing integer.
- No natural keys are used as primary keys, even where a natural unique key exists (e.g., `Department.code`, `User.email`) — those are modeled as separate `unique=True` columns instead.
- No UUID primary keys are in use anywhere in the current schema. If a future domain needs externally-exposed, non-enumerable identifiers (e.g., a public-facing student portal), that would be a deliberate per-table deviation, not a system-wide default — evaluate at the point that need actually arises rather than pre-adopting UUIDs everywhere.

## 5. Typing & Constraint Conventions

Observed conventions across `app/models/`, to be followed by any new domain model:

- **Strings**: `String(N)` with an explicit, deliberately-chosen length per field (e.g., `String(20)` for codes, `String(100)` for names/emails, `String(255)` for free-text `description`/`remarks`) — not unbounded `Text` or unlengthed `String`.
- **Optional text**: `Mapped[str | None] = mapped_column(String(255), nullable=True)` — the recurring pattern for `description`/`remarks` fields across nearly every domain entity.
- **Booleans**: `is_active: Mapped[bool] = mapped_column(Boolean, default=True)` is the standard soft-enable flag on reference/structural entities (Department, Program, Semester, Section, Course, Subject, Classroom, Examination, FeeStructure, TeacherAssignment). There is currently no corresponding soft-delete pattern for transactional entities (Attendance, ExamMark, FeePayment, Result) — deletion semantics for those are handled by domain-specific CRUD, not a shared column convention.
- **Money**: `Float` (`FeeStructure.amount`, `FeePayment.amount_paid`, `ExamMark.marks_obtained`, `Result.total_marks_obtained/total_max_marks/percentage`) — not `Numeric`/`Decimal`. This is a known precision tradeoff (binary floating point for currency and computed percentages), consistent with the project's existing intentional-tradeoff pattern (cf. `Student.phone` as `BigInteger` per Product Architecture's "Notable model decisions") — flagged here, not silently changed.
- **Dates/times**: `Date` for calendar dates (`enrollment_date`, `attendance_date`, `exam_date`, `payment_date`, session `start_date`/`end_date`), `Time` for wall-clock time-of-day (`Timetable.start_time/end_time`), `DateTime` reserved for actual timestamps (`Result.published_at`). No timezone-aware datetime usage currently — all naive.
- **Enums**: `User.role` uses a Python enum (`Role`) via SQLAlchemy's enum mapping — the only enum-typed column in the current schema. Other status-like fields (`AcademicSession.status`, `Enrollment.status`, `Result.status`, `Attendance.status`) are plain `String` with application-level valid-value sets rather than DB-level enums or `CHECK` constraints — an inconsistency worth deliberate resolution in a future decision, not fixed here.
- **Uniqueness**: applied where domain semantics require a natural key to be unique — `Department.name/code`, `Program.name/code`, `AcademicSession.session_name`, `Student.email`, `Teacher.email`, `User.email`. Composite uniqueness (e.g., "one ExamMark per student per examination", "one Attendance row per student per subject per date") is **not** currently enforced at the DB level anywhere — an application-level invariant only (consistent with Domain Architecture §6/§7's noted gaps).

## 6. Foreign Keys & Indexing

- Every FK column follows the pattern `mapped_column(ForeignKey("<table>.id"), index=True)` — FK columns are always indexed, since they're the standard join/filter path (a section's timetable, a student's enrollments, a session's fee structures, etc.).
- No `ON DELETE` behavior is explicitly specified on any FK today (defaults to Postgres's `NO ACTION`) — deleting a referenced row (e.g., a Department with Programs under it) will fail at the DB level rather than cascading. CRUD-layer delete operations are responsible for checking/guarding against this; there is no DB-level cascade or soft-delete safety net.
- Beyond FK columns, a small number of non-FK columns are indexed where they're a known high-frequency filter/sort key: `Attendance.attendance_date`, `Timetable.day_of_week`, `User.email`. New domain modules should index a column beyond its FKs only when there's a concrete query pattern (list/filter/sort, per the `GET /students`-style combined query pattern in Product Architecture) that needs it — not speculatively.

## 7. Migration Strategy (current and future)

**Current state**: additive-only, `create_all()`-driven for new tables; manual, untracked `ALTER TABLE` for changes to existing tables.

**When this stops being sufficient** (this system will hit these limits soon, given the module count already in place):
- Any column rename, type change, or `NOT NULL` addition to a populated table needs a reviewed, repeatable migration — manual `ALTER TABLE` run once by one person against one environment does not give you that.
- Multi-environment consistency (dev / staging / prod, if those come to exist) cannot be guaranteed without a migration history table recording what's been applied where.

**Recommended direction** (not adopted in this session — this is guidance for a future, explicitly-scoped task, per CLAUDE.md's "never implement future roadmap features automatically"):
- Introduce Alembic, initialized against the current schema as a baseline (`alembic stamp head` against the existing DB state, not a fresh `create_all()` replay).
- Once Alembic is adopted, `Base.metadata.create_all()` in `main.py` should be removed in favor of `alembic upgrade head` as part of deploy — running both mechanisms side by side would create drift between what `create_all()` thinks the schema is and what the migration history says it is.
- This is intentionally a separate future task, not scoped or started here.

## 8. Known Gaps (documented, not fixed in this session)

- No migration tool (Alembic or otherwise) — see §7.
- `echo=True` is hardcoded on the engine rather than gated by an environment/debug flag — will be noisy and potentially leak query parameter values into logs in a non-dev deployment.
- No `ON DELETE` cascade/restrict strategy defined per-relationship — currently defaults to DB-level `NO ACTION` everywhere, which may not match every relationship's intended delete semantics (e.g., should deleting an `Examination` cascade to its `ExamMark` rows, or be blocked?). Left for a future decision, not resolved here.
- No DB-level composite uniqueness or `CHECK` constraints for cross-field invariants noted in Domain Architecture §6/§7 (Section↔Program/Semester consistency, one-ExamMark-per-student-per-exam, etc.) — all application-level only.
- Money/percentage fields use `Float`, not `Numeric` — acceptable today, worth revisiting if Fees/Results calculations show rounding-related bugs in practice.

These are candidates for `docs/06_DECISIONS/` entries in future sessions, per the documentation structure proposed in Product Architecture §10.
