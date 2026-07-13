# EduCore SMS — Microservice Evolution

Status: living document. A direction, not a commitment or a scoped task — no extraction work is planned or started. Documentation only — no code, services, or infrastructure created or changed by this session, per CLAUDE.md's "never implement future roadmap features automatically." Builds on [01_PRODUCT_ARCHITECTURE.md](01_PRODUCT_ARCHITECTURE.md) through [08_DEPLOYMENT_ARCHITECTURE.md](08_DEPLOYMENT_ARCHITECTURE.md).

## 1. Purpose

Product Architecture §7 named candidate microservice boundaries at a glance. Deployment Architecture §7 named Dashboard's read-heavy aggregation as the most concrete near-term scaling lever. This document goes one level deeper: *how* an extraction would actually happen — the shared-data problem, an extraction order with reasoning, the strangler-fig migration approach, and what should explicitly never be split. It exists so that if/when extraction is ever scoped, it starts from a considered plan instead of an ad-hoc first attempt.

**This system should stay a modular monolith today.** Nothing in Sessions 1–8 identifies an actual scaling or team-boundary pain point that justifies extraction now (Product Architecture §1: single-institution scope; Deployment Architecture §7: scaling isn't an active concern). This document is deliberately speculative/preparatory, not a recommendation to act.

## 2. The Core Obstacle: AcademicSession as Shared Kernel

Domain Architecture §4 already identified this: `AcademicSession` is the most heavily-referenced entity in the system — Enrollment, TeacherAssignment, Timetable, Attendance, Examination, and FeeStructure all pin to it as their time-partitioning key. This is the single fact that makes microservice extraction hard here, and it needs to be named explicitly before any extraction ordering makes sense:

- Any service extracted while `AcademicSession` stays in the "core" database needs cross-service reads of `AcademicSession` (and typically also `Program`/`Semester`/`Section`, the rest of the Academic Structure tree) just to validate its own writes.
- This is the textbook "shared kernel" problem in domain-driven design: Academic Structure isn't really a peer bounded context to Fees or Examination — it's closer to reference data that every other context depends on.
- Two honest options when a domain *is* extracted: (a) the extracted service calls back into the core service for Academic Structure lookups (adds latency + a hard runtime dependency), or (b) the extracted service keeps a read-only, eventually-consistent local copy of the Academic Structure data it needs (adds replication complexity, but removes the runtime coupling). Neither is free. This tradeoff should be made explicitly, per extracted service, not assumed away.

Because of this, **Academic Structure and People (Student/Teacher) are expected to remain part of the core service indefinitely** (Product Architecture §7) — extracting them first would maximize cross-service chatter for every other domain, not reduce it.

## 3. Extraction Candidates, Re-Examined

Restating Product Architecture §7's ordering with the added reasoning from the shared-kernel problem (§2) and the actual FK/coupling picture from Domain Architecture §4:

| Order | Domain | Why this position |
|---|---|---|
| 1 | **Fees** | Lowest coupling to the rest of the system beyond Academic Structure + Student — `FeeStructure`/`FeePayment` don't feed data back into any other domain's writes (Domain Architecture §5: nothing depends on Fees). Distinct compliance/audit lifecycle. Best first candidate precisely because getting it wrong is contained. |
| 2 | **Examination & Results** | Bursty load (exam windows), distinct backup/retention needs (Product Architecture §7). Slightly more coupled than Fees — `Result` is a computed rollup that depends on `ExamMark`, both would need to move together (they're one bounded context, not two, despite being separate tables — Domain Architecture §3.7). |
| 3 | **Attendance** | High write volume, single-entity domain (no internal aggregation dependency like Result⇢ExamMark), but depends on `User` (Identity) for `marked_by_id` — the first candidate that touches the Identity shared-kernel question, not just the Academic Structure one. |
| 4 | **Dashboard/Reporting** | Read-only by construction (Domain Architecture §3.9) — the *easiest* to extract technically (no write-consistency concerns at all), but only worth doing once there's enough aggregate query load to justify a dedicated read-replica-backed service (Deployment Architecture §7). Ordered after the write-side extractions because splitting a read-aggregator before its data sources have stabilized their own service boundaries means re-doing the aggregation wiring twice. |
| 5 | **Identity & Access** | Becomes a shared platform service consumed by everything else (Auth/RBAC), likely *last* — every other domain, extracted or not, depends on it for `get_current_user`/RBAC (Security Architecture §3/§6), so it's the entity with the most inbound coupling to unwind carefully, not the least. |
| — | **Academic Structure, People, Enrollment, Scheduling** | Expected to remain in the core service indefinitely (§2) — not a "later" extraction candidate, a *non*-candidate under the current shared-kernel shape. |

This ordering optimizes for **minimizing the shared-kernel problem's blast radius at each step**, not for extraction ease alone — Dashboard is technically easiest but ordered 4th because extracting it first would mean rebuilding its read wiring against every subsequent extraction.

## 4. Migration Approach: Strangler Fig, Not Big-Bang

Given the modular-monolith structure already in place (Product Architecture §3's clean module boundaries, Folder Structure §3's four-file convention), a strangler-fig approach is the natural fit — no rewrite is implied by any of this:

1. **Extract data ownership first, service second.** Move the target domain's tables to their own database/schema while the code *still runs in the same process*, accessing the new database via a distinct connection. This surfaces the shared-kernel dependency problem (§2) in isolation, before also dealing with network boundaries and deployment topology.
2. **Extract the module's router/crud/service into a separate deployable**, behind the same API surface (same paths, same `api_router` prefix structure per Folder Structure §5) — initially reachable only via the original monolith proxying to it, so no client-visible contract changes.
3. **Cut over traffic directly to the new service**, retiring the proxy once the new service has run in parallel long enough to build confidence.
4. **Repeat per domain**, in the order from §3 — never multiple domains at once, consistent with CLAUDE.md's "one module at a time" development philosophy (Development Workflow §6) extended to the service-extraction scale.

Each step is independently reversible — a domain can stop at step 1 (separate schema, same process) indefinitely if step 2/3 turns out not to be worth it. Nothing forces a domain all the way to a separate deployable just because its data was separated.

## 5. Inter-Service Communication (direction, not adopted)

Once any service is actually extracted, the shared-kernel reads (§2) and any cross-domain writes need a defined communication style:

- **Synchronous (HTTP/gRPC) for reads that must be strongly consistent** — e.g., Fees validating a `program_id`/`semester_id` against Academic Structure at write time.
- **Asynchronous (event-driven) for cross-domain side effects that can tolerate eventual consistency** — e.g., a `StudentEnrolled` event that a future Attendance or Fees service reacts to, rather than those services synchronously calling Enrollment on every relevant read.
- No message broker, event bus, or service-mesh technology is selected here — that's an implementation decision for whichever future task actually begins extraction, not something to pre-select in a preparatory architecture document.

## 6. What Should Never Be Split

Naming the inverse explicitly, since "everything could theoretically be a microservice" is not useful guidance on its own:

- **Academic Structure + People + Enrollment + Scheduling** (§2/§3) — the shared-kernel core. Splitting these multiplies cross-service chatter for every other domain without reducing it for any of them.
- **Result and ExamMark** — always move together if Examination ever splits; `Result` has no independent existence without `ExamMark` data to aggregate (Domain Architecture §3.7).
- **RBAC and the User model** — Security Architecture §6/§8 already notes RBAC is role-based, not resource-owned, and every domain's authorization check depends on `get_current_user`. Splitting Identity before every other consumer has a stable way to validate tokens across a service boundary (token introspection, shared JWT verification, etc. — not designed here) would break authorization everywhere simultaneously.

## 7. Preconditions Before Any Extraction Begins

None of these exist yet — restated from prior sessions, not new findings, but worth collecting in one place since they're all *prerequisites* to this document's plan, not independent nice-to-haves:

- Dependency manifest + CI (Automation Strategy §3.1/§3.5) — a second deployable multiplies the cost of not having reproducible builds.
- Alembic migrations (Automation Strategy §3.2, Database Strategy §7) — two databases with untracked manual schema changes is materially worse than one.
- A defined deployment target (Deployment Architecture §6) — extraction produces a second thing that needs to be deployed; that needs to be possible at all first.
- A settled decision on whether the SaaS/multi-tenant direction (Product Architecture §7) is actually being pursued — extraction ordering and shared-kernel handling would look different under multi-tenancy (e.g., Academic Structure might need per-tenant partitioning even within the core service) than under continued single-tenant scope.

## 8. Known Gaps / Open Questions in This Strategy

- No inter-service authentication design (service-to-service token validation) is specified — flagged in §6 as a hard blocker for Identity extraction specifically, but not designed here.
- No decision on synchronous-call fallback/circuit-breaking behavior for the shared-kernel reads in §2 — if the core service is briefly unavailable, does Fees creation just fail, or degrade some other way? Not decided.
- This document assumes extraction happens *within* the current single-tenant scope; a SaaS pivot (Product Architecture §7) would likely require re-deriving this entire document rather than layering on top of it, since tenant isolation changes what "shared kernel" even means.

This document is a candidate for supersession by a `docs/06_DECISIONS/` ADR the moment any specific extraction is actually scoped — at that point the decision record should reference this document's reasoning rather than repeat it, and should update this document if the actual extraction reveals the ordering or approach here was wrong.
