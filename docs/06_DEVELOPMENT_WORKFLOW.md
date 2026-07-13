# EduCore SMS — Development Workflow

Status: living document. Reflects the actual git/branch/commit conventions observed in this repository as of 2026-07-13. Documentation only — no code, APIs, or DB schema created or changed by this session. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [05_SECURITY_ARCHITECTURE.md](05_SECURITY_ARCHITECTURE.md).

## 1. Purpose

Sessions 1–5 documented what the system *is*. This document describes how it actually gets built: the branching model, commit conventions, sprint cadence, and local verification steps already in use — observed from `git log`/`git branch`, not prescribed from scratch — plus the standing coding rules from `CLAUDE.md` that govern how work is scoped.

## 2. Branching Model

Observed branches: `main`, plus one `feature/<domain>` branch per module (`feature/enrollment`, `feature/examination`, `feature/fees`, `feature/result`, `feature/teacher-assignment`, `feature/timetable`), and one `refactor/<change>` branch for a cross-cutting change (`refactor/central-router-registration`, the current branch).

Convention:
- **`main`** — the integration branch; always expected to be in a runnable state (`import app.main` succeeds, server boots).
- **`feature/<domain-name>`** — one branch per new domain module (Teacher Assignment, Timetable, Enrollment, Examination, Result, Fees, etc.), named after the module it adds. Matches the one-module-per-branch granularity implied by CLAUDE.md's Roadmap ("Teacher module, then JWT Authentication, RBAC, Dashboard, Attendance, Course... one at a time").
- **`refactor/<change-name>`** — used for structural changes that aren't a new domain module (e.g., the current central router registration cleanup). Kept separate from feature branches so a refactor's diff isn't mixed with new functionality.
- Some feature branches were merged into `main` via an explicit merge commit (`c9f6363 Merge branch 'feature/timetable'`, `0867664 Merge branch 'feature/teacher-assignment'`); others (Examination, Result, Fees) appear as direct/fast-forwarded commits on `main` without a preserved merge commit. Both have occurred in this repo's history — not a strict rule to date, but explicit merge commits are the more traceable of the two and are the pattern to prefer going forward for anything non-trivial.

## 3. Commit Convention

Observed commit message pattern for module additions: **`Add <Module> module (Sprint <N>)`** — e.g., `Add Fees module (Sprint 15)`, `Add Result module (Sprint 14)`, `Add Examination module, with Exam Mark entry (Sprint 13)`. Earlier history shows the same pattern without merge commits (`Add Department module (Sprint 2)` through `Add Timetable module, with supporting Classroom entity (Sprint 12)`), plus one structural commit (`Register Department through Section routers in main.py`) for router wiring that didn't warrant its own "module" label.

Convention to follow for new work:
- New domain module: `Add <Module> module (Sprint <N>)`, incrementing `<N>` sequentially from the last used sprint number (15, per the most recent commit at the time of this document).
- A module that includes a closely-related supporting entity can note it in the same commit message (cf. Timetable + Classroom, Examination + Exam Mark) rather than splitting into two commits, when the supporting entity has no independent purpose outside that module.
- Structural/cross-cutting changes (router registration, shared middleware, etc.) get a plain descriptive commit message, no "Sprint" label, since they aren't a sprint deliverable in the roadmap sense.

## 4. Sprint Cadence

The commit history encodes an implicit sprint-per-module cadence, one sprint number per module, in the same order as CLAUDE.md's roadmap intent:

| Sprint | Module |
|---|---|
| 1 | Academic Session |
| 2 | Department |
| 3 | Program |
| 4 | Semester |
| 5 | Course |
| 6 | Subject |
| 7 | Attendance |
| 8 | Section |
| 9 | *(Teacher — implied; not visible in the sampled log window)* |
| 10 | Enrollment |
| 11 | Teacher Assignment |
| 12 | Timetable (+ Classroom) |
| 13 | Examination (+ Exam Mark) |
| 14 | Result |
| 15 | Fees |

This numbering is a project-tracking convention, not an architectural concern — recorded here so future sessions/tasks can pick the next sprint number correctly rather than guessing or colliding.

## 5. Local Verification Workflow

Per `CLAUDE.md` (restated here for a single workflow reference, not duplicated logic):

```bash
# Run the dev server (auto-reload)
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000

# Quick import/sanity check (also creates missing tables via Base.metadata.create_all)
./.venv/Scripts/python.exe -c "import app.main; print('IMPORT OK')"
```

- No test suite or linter is configured. Verification is manual: run the server, exercise endpoints via `curl` or the interactive docs at `http://127.0.0.1:8000/docs`.
- The import sanity check doubles as a schema-creation step (`create_all()` runs on import) — running it after adding a new model is the fastest way to confirm the model is both importable and registered for table creation (Database Strategy §3).
- No CI pipeline is configured in this repository at present — verification is entirely local and manual today.

## 6. Standing Coding Rules

Restated from `CLAUDE.md` as the operative constraints on every development session (not new rules — this section exists so Session 6 is a complete workflow reference without requiring a second lookup):

- Follow FastAPI best practices; SQLAlchemy ORM; Pydantic v2; type hints throughout.
- Modify only the files required for the current task — never rewrite completed modules or touch unrelated code.
- Never regenerate the whole project or change the folder structure unless explicitly asked.
- Never implement future roadmap features automatically — wait for the next explicit task.
- Schema changes to existing tables require a manual `ALTER TABLE` (Database Strategy §3/§7) — `create_all()` will not pick up column changes on tables that already exist.

## 7. Adding a New Module — End-to-End Workflow

Combining the technical checklist (Folder Structure §6) with the process conventions in this document:

1. Branch: `git checkout -b feature/<domain-name>` off `main`.
2. Implement per the four-file convention (Folder Structure §3) — model, schema, crud, router — and register the model in `main.py`'s import block and the router in `app/routers/__init__.py` (Folder Structure §5).
3. Verify locally: import sanity check, then run the server and exercise the new endpoints via `/docs` (§5).
4. Commit: `Add <Module> module (Sprint <N>)`, `<N>` = next sequential sprint number (§3/§4).
5. Merge to `main` via an explicit merge commit (§2) once the module is verified working end-to-end.

This workflow is descriptive of established practice in this repository, not a new process being introduced — it's recorded here so it's consistently followed rather than reconstructed from `git log` each time.

## 8. Known Gaps (documented, not fixed in this session)

- No CI/CD pipeline — all verification is local and manual (§5).
- No linter or formatter configured (e.g., ruff, black, mypy) — code style consistency currently relies on convention alone, not tooling.
- No `requirements.txt`/`pyproject.toml` — dependencies exist only in `.venv`, meaning the environment isn't reproducible from a fresh clone without manually discovering what's installed (also noted in CLAUDE.md).
- Merge-commit-vs-fast-forward practice has been inconsistent historically (§2) — worth deciding on one going forward rather than fixing the existing history.
- Sprint numbering has at least one gap in the visible log (Sprint 9 not present in the sampled range) — not investigated further in this session; noted so a future session doesn't misassume sprint numbers are fully contiguous without checking full history.

These are candidates for `docs/06_DECISIONS/`-style follow-up (per Product Architecture §10) in a future session — no tooling, CI, or dependency-management changes are made here.
