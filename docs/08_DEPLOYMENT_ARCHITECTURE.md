# EduCore SMS — Deployment Architecture

Status: living document. Reflects the actual (dev-only) deployment posture as of 2026-07-13, plus a direction for what's missing. Documentation only — no containerization, CI/CD, infrastructure, or config files created or changed by this session, per CLAUDE.md's "never implement future roadmap features automatically." Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [07_AUTOMATION_STRATEGY.md](07_AUTOMATION_STRATEGY.md).

## 1. Purpose

Automation Strategy §5 explicitly deferred deployment/infrastructure automation to this session. This document describes the current deployment reality (there isn't one beyond local dev), the topology implied by the architecture so far, and a direction for environments, configuration, and release process — without adopting or implementing any of it.

## 2. Current State: Local Development Only

There is no deployed environment today. The entire "deployment" surface is:

```bash
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

- Single process, single machine, `--reload` (dev-only, watches for file changes — never appropriate for a real deployment).
- Postgres is assumed to be reachable at whatever `DATABASE_HOST/PORT/NAME/USER/PASSWORD` resolve to in `.env` (Database Strategy §2) — presumably a local or developer-provisioned instance; nothing in the repo describes how that Postgres instance itself is stood up.
- No containerization (no `Dockerfile`/`docker-compose.yml`), no process manager (no systemd unit, no supervisor config, no `Procfile`), no reverse proxy configuration, no TLS termination — none of these exist in the repository, and none are assumed by anything documented so far.
- `Base.metadata.create_all()` running at every startup (Database Strategy §3) is itself a dev-oriented behavior — acceptable when there's one developer and one throwaway DB, actively risky as a "deployment strategy" once a migration tool is adopted (Automation Strategy §3.2), since the two mechanisms must not run against the same database.

This document exists to give a name to what's currently informal, and a direction for closing the gap — not to claim a deployment pipeline exists.

## 3. Deployment Topology (current, single environment)

```
Developer machine
  └─ uvicorn (app.main:app) ── :8000
       └─ Postgres (single instance, single DB, single schema)
```

No load balancer, no multiple app instances, no caching layer, no CDN, no separate static-asset serving (the API has no static assets to serve — it's JSON-only, per Security Architecture §7's response envelope). This is appropriate for the system's current single-institution, pre-production scope (Product Architecture §1) and should not be over-built ahead of actual need.

## 4. Target Environment Model (direction, not adopted)

A conventional three-environment progression, matching the single-tenant scope from Product Architecture §1 (no per-tenant environment multiplication needed unless/until the SaaS direction in Product Architecture §7 is actually pursued):

| Environment | Purpose | Notes |
|---|---|---|
| **Local/dev** | Individual development | Current state (§2) — `--reload`, `create_all()`, local Postgres. |
| **Staging** | Pre-release verification against a production-like setup | Would be the first environment to actually require the automation from Automation Strategy §3 (reproducible dependency install, Alembic migrations run explicitly rather than via `create_all()`, CI-gated deploy). |
| **Production** | The live system | `--reload` off, `create_all()` retired in favor of Alembic (Database Strategy §7), `engine.echo` off or gated (Security Architecture §8 flagged this as a logging-sensitivity issue, not just a noise issue), secrets sourced from a secrets manager rather than a committed `.env`. |

Each environment differs only in configuration (Product Architecture §5's `Settings` object is exactly the seam this depends on — it already centralizes every env-varying value except `engine.echo`, which is currently hardcoded rather than settings-driven; see §6) and in which automation gates apply, not in application code or folder structure.

## 5. Configuration & Secrets Strategy (direction)

Building on Database Strategy §2 and Security Architecture §5:

- **Already correct**: all environment-varying values (DB connection, `secret_key`, `algorithm`, token expiry) are read exclusively through `Settings` (`app/core/config.py`), sourced from `.env`. This is the right seam for per-environment configuration — nothing needs to change structurally to support multiple environments, only *how* `.env`'s values are supplied per environment.
- **Gap**: `.env` today is presumably a local file (not committed, per standard practice, though this session did not verify `.gitignore` contents). In a staging/production setup, secrets (`secret_key`, `database_password`) should come from a secrets manager or the deployment platform's environment-variable injection, not a file checked into or shipped alongside the deployment artifact.
- **Gap**: `engine.echo=True` (Database Strategy §8, Security Architecture §8) is hardcoded in `app/core/database.py`, not read from `Settings`. Before any non-dev environment exists, this needs to become an environment-driven flag rather than a constant — otherwise every environment either logs full SQL (noisy, and a query-parameter disclosure risk per Security Architecture §8) or someone has to remember to hand-edit the source per environment, which defeats the purpose of `Settings` existing at all.

## 6. Release Process (direction)

Depends on Automation Strategy §3 items being adopted first — a release process without CI (§3.5) or migrations (§3.2) is just "manually copy files and hope," which is where the project effectively is today. Direction, in dependency order:

1. Dependency manifest + Alembic baseline (Automation Strategy §3.1/§3.2) — a release artifact needs a reproducible install and an explicit migration step, not `create_all()`.
2. CI gate (Automation Strategy §3.5) — a release should not ship without at least the import sanity check and (once it exists) the test suite passing.
3. A defined deploy step — explicitly not scoped here: containerization vs. bare-metal/VM vs. PaaS is an open choice that depends on hosting decisions not yet made, and shouldn't be pre-selected in an architecture doc ahead of that decision.
4. Migration application as an explicit release step (`alembic upgrade head`), separate from and prior to starting the new application version — never inferred implicitly from `create_all()` at app boot in any environment beyond local dev.

## 7. Scaling Considerations (light-touch, not a current need)

Noted for completeness, not because scaling is an active concern at the current single-institution scope (Product Architecture §1):

- The app is stateless per request (JWT auth, no server-side session — Security Architecture §5), so horizontal scaling of the app process itself is not architecturally blocked whenever it becomes relevant.
- Postgres is the only stateful component and the only place scaling would need real design work (connection pooling, read replicas for Dashboard's read-heavy aggregation queries — Product Architecture §7 already flagged Dashboard as "a natural fit for a separate read-replica-backed service" as a *future microservice* direction, which is the more relevant scaling lever than scaling the monolith itself).
- None of this is being sized, planned, or committed to in this session — it's recorded so a future session doesn't have to rediscover that the app layer is already scaling-friendly by construction.

## 8. Known Gaps (documented, not fixed in this session)

- No containerization, process manager, or reverse-proxy config exists anywhere in the repo.
- No CI/CD pipeline (restated from Automation Strategy §3.5 — deployment automation depends on it).
- `engine.echo` is hardcoded rather than `Settings`-driven (§5) — the one concrete piece of config debt blocking a clean multi-environment story, since every other setting already goes through `Settings`.
- No documented process for provisioning the Postgres instance itself (schema creation is covered by Database Strategy §3, but instance provisioning/backups/access control is not addressed anywhere in the docs so far).
- No health-check beyond the root `/` endpoint (`app/main.py`'s `health_check`) — sufficient for manual verification today, not necessarily sufficient for a real deployment platform's liveness/readiness probe conventions (e.g., no DB-connectivity check in the health endpoint).

These are candidates for `docs/06_DECISIONS/`-style follow-up once a concrete deployment target (hosting platform, containerization approach) is actually chosen — no infrastructure decisions are made in this session.
