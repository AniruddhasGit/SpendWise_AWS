# SW-ADR-065 — The connection pool is sized explicitly and exposed

| Field | Value |
|---|---|
| ADR | `SW-ADR-065` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §11.3` · `SW-ADR-008` |

## Context

SRC-001 §11.3 fixes uvicorn at two workers, so the pool is multiplied by two per task before any scaling, plus the migration connection and the client's own psql sessions. A db.t4g.micro offers roughly 110 connections. Connection exhaustion presents as intermittent request failures, not a clean error.

## Options considered

- A. pool_size 5, max_overflow 5, both exposed as env vars, with the arithmetic written down.
- B. SQLAlchemy defaults.
- C. NullPool.

## Decision

**A.**

## Consequences

- The number matters less than the fact that it was chosen, is visible, and can be changed without a deploy.
- Arithmetic: 2 workers x (5+5) = 20 per task, plus 1 migration connection at boot, plus the operator's own sessions.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
