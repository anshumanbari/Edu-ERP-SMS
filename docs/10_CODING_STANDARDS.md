# EduCore SMS — Coding Standards

Status: living document. Codifies the coding style already observed across `app/` as of 2026-07-13, plus explicit rules against AI-generated-looking ("vibe coded") patterns. Documentation only — no code changed by this session. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [09_MICROSERVICE_EVOLUTION.md](09_MICROSERVICE_EVOLUTION.md).

## 1. Purpose

The goal of this document is a single sentence: **code should read like a competent engineer wrote it deliberately, not like it was generated to satisfy a prompt.** Every rule below either (a) restates a pattern already consistently present in this codebase, or (b) names an anti-pattern to actively avoid. This is the enforcement-by-convention layer that Automation Strategy §3.4 noted doesn't yet exist as tooling (no ruff/mypy) — until that lands, this document is what code review checks against.

## 2. What "Vibe Coded" Looks Like — and Why It's Rejected Here

Recognizable failure modes to avoid, stated plainly so they're easy to spot in review:

- **Comments that narrate the obvious.** `# increment counter` above `count += 1`. If removing a comment loses no information a competent reader wouldn't already have, delete it.
- **Defensive code for impossible states.** `if student is None: raise ...` immediately after a query that already guarantees a result, or `try/except` around code that cannot raise. This looks careful; it's actually noise that hides where real error handling matters.
- **Speculative abstraction.** A `BaseRepository` class introduced for one CRUD module "in case we need it later." CLAUDE.md already forbids this ("no half-finished implementations," "don't design for hypothetical future requirements") — restated here because it's the single most common tell of generated-not-written code.
- **Inconsistent idiom within one file.** Half the functions use `db.query(Model).filter(...)`, the other half use `select(Model).where(...)` in the same file, because each was generated independently without regard to its neighbor. Pick the idiom already in use in that file/module and match it — do not introduce a second style "because it's more modern."
- **Renaming or restating instead of deleting.** Prefixing an unused variable with `_` instead of removing it, leaving a `# removed: old logic` comment where code used to be, keeping a re-exported type nobody imports. CLAUDE.md forbids these explicitly — restated here as a coding-standards violation, not just a housekeeping one.
- **Uniform verbosity regardless of complexity.** Every function getting the same five-line docstring whether it's a one-line passthrough or genuinely non-obvious logic. Match documentation effort to actual complexity (§4).
- **Error messages that describe the code instead of the problem.** `"Error in create_student function"` instead of `"A student with email 'x@y.com' is already registered."` (the actual pattern in this codebase — see `crud/student.py`). Error messages are for the caller/API consumer, not a debugging breadcrumb for the author.

None of these are hypothetical — they're the specific shapes of output that make code reviewable-at-a-glance turn into code that needs archaeology. The standards below are the positive version of avoiding them.

## 3. Observed Conventions (already in place — follow, don't reinvent)

Pulled directly from the codebase, not proposed fresh:

- **Section-header comments** in `crud/` and `routers/` files, delimiting logical groups (`# CREATE`, `# READ — all`, `# UPDATE`, `# DELETE` in `crud/student.py`; similar per-endpoint dividers in `routers/auth.py`) using a fixed-width `# ---...---` rule. This is the one place a "decorative" comment style is established practice here — keep using it for new CRUD/router files, since consistency with existing files matters more than any individual preference.
- **Structured docstrings** on CRUD functions and router endpoints: a one-line summary, then `Args:`/`Raises:`/`Returns:` (CRUD) or a markdown-bulleted field description plus `Raises **NNN**:` callouts (routers, matching FastAPI's OpenAPI rendering — see `routers/auth.py`). Match whichever of these two shapes is already used in the file you're editing.
- **Type hints everywhere** — `Mapped[]` on models, full parameter/return annotations on every function. Not optional, not "where convenient."
- **Bounded, explicit types** over convenient-but-loose ones — `String(100)` not unbounded `Text`, `Literal["asc", "desc"]` not bare `str`, `Role` enum not a raw string for role fields (Database Strategy §5). When a new field's valid values are a known, closed set, express that in the type, not in a comment describing the valid values.
- **HTTPException/AppException raised at the point of violation**, not caught-and-rethrown or wrapped — see `crud/student.py`'s 409 check happening inline, immediately before the insert it protects, not as a separate validation layer.

## 4. Documentation Effort Should Match Complexity

Per CLAUDE.md's default ("no comments unless the WHY is non-obvious") reconciled with the observed docstring convention (§3) — the two aren't in tension once effort is calibrated correctly:

- A CRUD function with a real precondition (uniqueness check, a non-obvious status transition) gets the full `Args`/`Raises`/`Returns` docstring — this *is* the non-obvious WHY, documented at the right altitude.
- A trivial passthrough (`get_all_students` doing exactly what its name says) still gets the short form for consistency with its neighbors in the same file, but should not accumulate speculative detail it doesn't need.
- Inline comments (not docstrings) are reserved for the CLAUDE.md standard: a hidden constraint, a workaround, a subtle invariant. `Student.phone` being `BigInteger` despite the general best practice being `String` (Product Architecture's "Notable model decisions") is exactly the kind of thing that earns an inline comment — it's surprising and would cost a future reader real time to rediscover.

## 5. Naming

- Files, functions, and variables follow the domain vocabulary established in Domain Architecture §3 — a `Section` is always a `Section` (never `Sec`, `Grp`, or `Class` in code, even though "class" is colloquially accurate), a `Semester` is always `semester_id` in FK columns, never `sem_id`. Consistency with the domain model's own naming outranks brevity.
- Router path operation function names follow the existing `get_all_<domain>s` / `get_<domain>_by_id` / `create_<domain>` / `update_<domain>` / `delete_<domain>` pattern — a new module's router should be guessable by someone who's read one other router, not independently invented.
- Boolean fields are named as predicates (`is_active`, `is_current`, `is_published`) — never `active_flag`, `status_bool`, or similar.

## 6. Function & File Size

- One file per domain entity per layer (Folder Structure §3) already bounds file size naturally — a `crud/<domain>.py` file with CRUD-plus-one-or-two-domain-specific-queries is the expected shape. A file that's grown far beyond its siblings' size is a signal that a concern has crept in that belongs elsewhere (e.g., cross-domain aggregation belongs in `dashboard/services/`, not bolted onto a domain's own CRUD file — Product Architecture §3).
- A CRUD function does one query/mutation plus its immediate precondition checks — not multiple unrelated operations bundled because they happened to be needed by the same caller. If two callers need different combinations of the same checks, that's two functions, not one function with branching flags.

## 7. Consistency Over Personal Preference

The single overriding rule, restated because it's the actual mechanism by which "vibe coded" is avoided: **when extending an existing module, match that module's existing style exactly**, even where this document's stated preference differs slightly, unless the task is specifically to fix a style inconsistency. A codebase where every file independently reflects "current best judgment" reads as generated; a codebase where new code is indistinguishable in style from the code around it reads as human-maintained. When adding a genuinely new pattern (no precedent in the codebase to match), follow this document, then apply it consistently to every subsequent file so it becomes precedent for the next person.

## 8. Review Checklist

A quick pass for any new or modified file before it's considered done:

- [ ] No comment states something the code already makes obvious.
- [ ] No error handling exists for a state that cannot occur given the code above it.
- [ ] No abstraction exists that has exactly one current caller and no stated second use case.
- [ ] Docstring/comment style matches the file's existing siblings, not a different convention introduced fresh.
- [ ] No renamed-instead-of-deleted dead code (`_unused`, `# removed:` comments, orphaned re-exports).
- [ ] Types are as narrow as the domain actually requires (`Literal`, `Enum`, bounded `String`), not loosened for convenience.
- [ ] Naming matches Domain Architecture §3's vocabulary and the existing router/crud naming pattern (§5).
- [ ] The file's size/shape is consistent with its siblings in the same layer — no unrelated concerns bolted on.

## 9. Known Gaps

- These standards are currently enforced only by human code review — Automation Strategy §3.4 already flagged the absence of `ruff`/`mypy`, which is where a subset of this document (typing narrowness, unused-variable detection, formatting consistency) would eventually move from "checklist" to "CI gate." Until then, §8's checklist is the actual enforcement mechanism.
- This document doesn't cover test code style, since no test suite exists yet (Development Workflow §8) — a future session should extend this document once Automation Strategy §3.3 is adopted, rather than guessing test conventions ahead of the first test file being written.
