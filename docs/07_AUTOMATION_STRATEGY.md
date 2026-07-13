# EduCore SMS — Automation Strategy

Status: living document. Proposes a direction for automation based on gaps already identified in Sessions 1–6. Documentation only — no CI config, scripts, hooks, or dependency files created or changed by this session, per CLAUDE.md's "never implement future roadmap features automatically." Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [06_DEVELOPMENT_WORKFLOW.md](06_DEVELOPMENT_WORKFLOW.md).

## 1. Purpose

Development Workflow §8 and Database Strategy §7/§8 each flagged the same underlying fact from different angles: nothing in this repository runs automatically. There is no CI, no test suite, no linter, no migration tool, no dependency manifest, and no scaffolding for the highly repetitive four-file-per-domain pattern. This document consolidates those gaps into one prioritized automation strategy, so future sessions implement automation deliberately and in order, rather than piecemeal.

This is a strategy document, not an implementation. Nothing here is adopted until an explicit future task scopes it in — consistent with every prior session's "known gaps, not fixed here" convention.

## 2. Why Automation, and Why Now

The module count (18 domain entities plus Auth/Identity and Dashboard, per Domain Architecture) has passed the point where manual-only verification scales. Two concrete symptoms already on record:
- Database Strategy §7: manual `ALTER TABLE` with no tracked history is "the single biggest schema-lifecycle risk in the current setup" — this gets worse, not better, with every additional module.
- Development Workflow §8: no reproducible environment (`.venv`-only dependencies) and no CI means every verification claim ("it works") is only as good as one person's local machine at one point in time.

Automation strategy here means: reduce reliance on a human remembering to run the right manual step, in the order the module-per-domain convention actually requires.

## 3. Automation Categories

### 3.1 Dependency Reproducibility
**Gap** (Development Workflow §8): no `requirements.txt`/`pyproject.toml`; dependencies exist only in `.venv`.
**Direction**: freeze current `.venv` into a manifest (`pyproject.toml` preferred, given Pydantic v2/FastAPI's modern tooling expectations) as the first automation step — every other automation category (CI, pre-commit) depends on being able to reproduce the environment from source control first.

### 3.2 Schema Migrations
**Gap** (Database Strategy §7): `create_all()` is additive-only; existing-table changes are manual, untracked `ALTER TABLE`.
**Direction**: adopt Alembic, baselined against the current live schema (`alembic stamp head`, not a fresh replay) so migration history starts now rather than attempting to reconstruct 15 sprints of undocumented `ALTER TABLE` history. Once adopted, `create_all()` in `main.py` should be retired in favor of `alembic upgrade head` at deploy time (Database Strategy §7) — running both concurrently would let them drift.

### 3.3 Automated Testing
**Gap** (Development Workflow §5/§8): no test suite; verification is manual `curl`/`/docs` exercise per module.
**Direction**: given the four-file-per-domain convention (Folder Structure §3) and the combined-query reference pattern (`GET /students`, Product Architecture), tests are highly templatable per module: CRUD round-trip, RBAC-denial case (per role, per Security Architecture §6), and pagination/filter/sort behavior where applicable. A shared pytest fixture set (test DB session, authenticated client per role) would let each new module's test file be a small, mechanical addition rather than bespoke work — mirroring how the four-file convention already makes each new module a template-following addition on the implementation side.

### 3.4 Linting & Formatting
**Gap** (Development Workflow §8): no ruff/black/mypy; style consistency relies on convention alone.
**Direction**: `ruff` (lint + format in one tool) plus `mypy` for the `Mapped[]`-heavy ORM code (Database Strategy §5's typing conventions are currently enforced only by code review, not tooling). Low effort relative to the other categories — a reasonable first or second automation task once dependency reproducibility (§3.1) exists to pin tool versions.

### 3.5 CI Pipeline
**Gap** (Development Workflow §8): no CI; all verification is local.
**Direction**: CI is the category that *depends on* the others rather than standing alone — it needs §3.1 (reproducible install), and becomes meaningfully useful once §3.3/§3.4 exist to run. A CI pipeline before there's anything for it to run beyond the import sanity check (`import app.main`) has limited value; sequencing matters here more than in the other categories.

### 3.6 Module Scaffolding
**Not a currently-identified gap in prior sessions, but a natural consequence of Folder Structure §3/§6**: every new domain module is four files following an identical shape (model/schema/crud/router) plus two registration edits (`main.py` model import, `routers/__init__.py` router registration). This is mechanical enough to script (a generator that takes a domain name and produces the four skeleton files plus a checklist reminder for the two registration edits) — lower priority than §3.1–3.5 since it's a productivity aid, not a risk-reduction measure, but worth naming as a category in its own right.

## 4. Recommended Sequencing

Ordered by what unblocks what, not by effort:

1. **Dependency manifest** (§3.1) — everything else needs a reproducible install first.
2. **Alembic baseline** (§3.2) — highest-risk gap (Database Strategy's own words), and independent of testing/CI, so it can proceed in parallel with step 3 once step 1 is done.
3. **Linting/formatting** (§3.4) — quick to add once dependencies are pinned, immediately raises the floor on code review effort.
4. **Test suite** (§3.3) — the largest effort, but the four-file convention makes it templatable per module rather than open-ended.
5. **CI pipeline** (§3.5) — wires together 1, 3, and 4 into an automatic gate; adding it earlier than this just automates the import sanity check, which has limited value on its own.
6. **Module scaffolding** (§3.6) — pure productivity tooling, can be picked up whenever convenient; has no dependency on the others.

## 5. Non-Goals for This Strategy

- No deployment/infrastructure automation (containerization, hosting, secrets management) is addressed here — that belongs with a future Deployment Architecture session, not this one, and depends on decisions (single-tenant vs. SaaS, per Product Architecture §7) not yet made.
- No automated data-seeding/fixture strategy for manual QA is proposed here — related to but distinct from automated testing (§3.3), and lower priority given no CI exists yet to consume it.
- This document does not select specific tool versions or write any config — that's implementation, scoped to whichever future task picks up an item from §4.

## 6. Known Gaps in This Strategy Itself

- Sequencing in §4 assumes single-threaded execution (one task at a time, per CLAUDE.md's "one module at a time" convention); if multiple people work on this repository concurrently, dependency-manifest and Alembic-baseline work becomes more urgent and less parallelizable than stated here, since untracked local `.venv` drift or unbaselined schema changes compound faster with more contributors.
- No effort/time estimates are given — this is a priority ordering, not a project plan.

This document is a candidate for supersession by `docs/06_DECISIONS/` entries once individual items from §4 are actually scoped and adopted — at that point each adopted item should get its own ADR recording what was chosen and why, rather than this strategy document being treated as the permanent record.
