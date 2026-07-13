# EduCore SMS — Security Architecture

Status: living document. Reflects the actual security implementation as of 2026-07-13. Documentation only — no code, APIs, or DB schema created or changed by this session. Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [04_DATABASE_STRATEGY.md](04_DATABASE_STRATEGY.md).

## 1. Purpose

Product Architecture §6 named Auth (JWT) and Authorization (RBAC via dependencies) as platform components. This document is the detailed security architecture: the authentication flow, password handling, token lifecycle, the RBAC model and where it is (and isn't) applied, error/response handling, and known gaps.

## 2. Identity Model

- **`User`** (`app/models/user.py`) is the sole authenticable identity: `id, name, email(unique), hashed_password, role`. Per Domain Architecture §3.1, this is distinct from `Student`/`Teacher` profile records — a `User` account is not automatically linked to a `Student` or `Teacher` row today (see §8, Known Gaps).
- **`Role`** (`app/core/roles.py`) is a three-value `str` enum: `ADMIN`, `TEACHER`, `STUDENT`. It is the only enum-backed column in the schema (Database Strategy §5).

## 3. Authentication Flow

Implemented in `app/routers/auth.py` + `app/core/security.py`, all under the `/auth` prefix:

1. **`POST /auth/register`** — accepts `UserCreate` (name, email, password, optional role), delegates to `crud.create_user`. Self-registration is restricted at the schema level to `Role.STUDENT` or `Role.TEACHER` (`UserCreate.role: Literal[Role.STUDENT, Role.TEACHER]`) — an `admin` account cannot be created through this endpoint; admins must be provisioned some other way (not currently documented/scripted — see §8).
2. **`POST /auth/login`** — standard OAuth2 password flow (`OAuth2PasswordRequestForm`: `username`=email, `password`). Verifies credentials via `crud.authenticate_user`, returns a `Token` (JWT) on success, `401` on failure.
3. **`GET /auth/me`** — returns the profile of the caller identified by their bearer token, via `get_current_user`.

Token retrieval is wired through FastAPI's `OAuth2PasswordBearer(tokenUrl="/auth/login")`, which is also what drives the "Authorize" flow in the interactive `/docs` UI.

## 4. Password Handling

- Hashing: `bcrypt` directly (`bcrypt.hashpw`/`bcrypt.checkpw`), not passlib or another abstraction layer — `app/core/security.py`'s `hash_password`/`verify_password`.
- Password policy, enforced in `UserCreate` (`app/schemas/user.py`): 8–72 characters (72 is bcrypt's own input limit, correctly respected here rather than silently truncating), must contain at least one letter and one digit (`field_validator`). No complexity requirement beyond that (no symbol requirement, no rejection of common passwords).
- Plaintext passwords never persist — only `hashed_password` is stored on `User`; no plaintext logging path exists in the reviewed code.

## 5. Token Lifecycle

- **Type**: JWT (via `python-jose`), signed with `settings.secret_key` using `settings.algorithm` (both from `.env`, read only through `Settings` — Database Strategy §2 pattern extends to secrets too).
- **Claims**: `sub` (the user's email) and `exp` (expiry). No other claims (no `role`, no `jti`, no `iat`) are embedded in the token today — every authenticated request re-derives the user's role from the DB via `get_current_user`'s lookup, not from the token payload. This means a role change takes effect immediately on the *next* request rather than requiring token invalidation — a favorable consistency property, not a gap.
- **Expiry**: `settings.access_token_expire_minutes`, configured via `.env`. Single access-token model — **no refresh token** exists. When the access token expires, the client must call `/auth/login` again.
- **Revocation**: none. There is no denylist/blocklist, no `jti` tracking, and no server-side session state — a token is valid until it expires, full stop. This is a standard stateless-JWT tradeoff, but it means there is currently no way to force-logout a user or invalidate a compromised token before its natural expiry (see §8).
- **Transport**: `Authorization: Bearer <token>` header only — no cookie-based token storage in the current implementation.

## 6. Authorization (RBAC) Model

- **Mechanism**: `app/core/rbac.py`'s `require_roles(*allowed_roles)` — a dependency *factory* that returns a FastAPI dependency checking `current_user.role in allowed_roles`, raising `ForbiddenException` (403) otherwise. Declared per-route via `Depends(require_roles(Role.ADMIN, ...))`, consistent with Product Architecture §8's "RBAC at the router boundary" principle — authorization requirements are visible at each endpoint's definition, not inferred from middleware.
- **Granularity observed**: role checks are applied **per-mutating-operation, not uniformly across a router**. Pattern seen in `student.py`: create/update require `Role.ADMIN, Role.TEACHER`; delete requires `Role.ADMIN` only; reads (list/get-by-id) have no role dependency — any authenticated... actually, reads in `student.py` don't even show a `get_current_user`/`require_roles` dependency in the sampled lines, meaning **list/get endpoints may not require authentication at all** on some routers (see §8 — this needs verification per-router, not assumed uniform).
- **`fee_payment.py`** is stricter: every endpoint (including reads) requires `Role.ADMIN`.
- **`app/dashboard/router.py`** applies RBAC once, at the router level: `APIRouter(..., dependencies=[Depends(require_roles(Role.ADMIN, Role.TEACHER))])` — every dashboard endpoint inherits the same restriction. This is a cleaner pattern (one declaration covers the whole router) than the per-endpoint style used in most domain routers, worth considering as the standard for new modules.
- **No resource-level authorization** exists beyond role — e.g., a `TEACHER` role can act on any student/section/exam, not just ones they're assigned to (per `TeacherAssignment`). Role-based, not ownership-based, access control throughout.

## 7. Error Handling & Information Disclosure

- Centralized exception handling (`app/core/error_handlers.py`), registered once in `main.py`, four handlers:
  - `AppException` (and subclasses `NotFoundException`/`ConflictException`/`BadRequestException`/`UnauthorizedException`/`ForbiddenException`, `app/core/exceptions.py`) → the exception's own status/message.
  - `StarletteHTTPException` → passthrough with a consistent envelope.
  - `RequestValidationError` → `422` with Pydantic's error details included in the response (`details=jsonable_encoder(exc.errors())`) — informative for API consumers, standard practice, not a disclosure risk since it only echoes back the caller's own malformed input.
  - Unhandled `Exception` → generic `500`, message "An unexpected error occurred." with **no stack trace or internal detail leaked to the client**; full detail (`exc_info=exc`) goes to the server-side logger only. This is the correct pattern — verified, not assumed.
- All error responses share one envelope shape (`success`, `status_code`, `error`, `message`, `details`), and all successful responses are wrapped by `StandardResponseMiddleware` into a matching `success`/`status_code`/`message`/`data` shape — consistent API contract for both paths.
- `401` responses on invalid/expired tokens correctly include `WWW-Authenticate: Bearer` and a generic "Could not validate credentials." message — no distinction is leaked between "token expired," "token malformed," and "user doesn't exist," which is good practice (avoids user enumeration via token errors).
- `login` failure message ("Incorrect email or password.") is appropriately generic (doesn't reveal whether the email exists) — good practice. `register`'s `409 Conflict` on duplicate email is, by contrast, an intentional user-enumeration surface on the registration endpoint specifically — a common and generally accepted tradeoff for self-registration flows, not flagged as a defect.

## 8. Known Gaps (documented, not fixed in this session)

- **No refresh token / no revocation** — a compromised or leaked token is valid until natural expiry; no server-side kill switch (§5).
- **`User` ↔ `Student`/`Teacher` linkage is undefined** — nothing in the schema ties a logged-in `User` account to a specific `Student` or `Teacher` profile row. This matters for any future feature where a student should only see their own records — that's currently unbuildable without first deciding this linkage (candidate for a `docs/06_DECISIONS/` entry).
- **Admin provisioning path is undocumented** — since self-registration is capped at `student`/`teacher`, how the first/any `admin` account gets created is not specified anywhere in code or docs.
- **RBAC coverage is inconsistent across routers** — some routers protect only mutations, some (dashboard, fee_payment) protect everything including reads, and it wasn't verified in this session whether *every* router even applies `get_current_user` on its read endpoints (i.e., some list/get endpoints may be effectively unauthenticated). This needs an explicit per-router audit, not assumed from the two samples reviewed here.
- **Role is course/section-blind (RBAC only, no resource ownership)** — a `TEACHER` can act on any resource system-wide, not scoped to their own `TeacherAssignment`s (§6).
- **`engine.echo=True`** (Database Strategy §8) also has a security dimension: verbose SQL logging in a non-dev environment could log sensitive query parameter values (e.g., email lookups) into application logs.
- **No rate limiting** on `/auth/login` or `/auth/register` — brute-force/credential-stuffing and registration-spam are unmitigated at the application layer today.
- **No CORS configuration** is present in `main.py` — FastAPI's default (no CORS middleware registered) effectively blocks cross-origin browser access entirely rather than allowing a defined origin list; fine for a same-origin/API-only consumer today, but will need explicit configuration the moment a separate frontend origin is introduced.

These are candidates for `docs/06_DECISIONS/` entries in future sessions, per the documentation structure proposed in Product Architecture §10. No remediation is scoped or performed in this session.
