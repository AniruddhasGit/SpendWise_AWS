# SW-ADR-070 — Health and readiness: what each endpoint discloses

> **⚠ AMENDED 2026-08-05 by `SW-ADR-073` (QA FINDING-6 (HIGH)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-070` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §7.7` · `SW-ADR-014` · `SW-ADR-005` |

## Context

SRC-001 §7.7 justifies an unauthenticated, database-free /healthz by 'that's what the load balancer calls' — and SW-ADR-014 deleted the load balancer, so that caller no longer exists. Nothing revisited the endpoint afterwards. The deployment is a raw public IP over plain HTTP, so both endpoints are reachable by anyone who scans the address.

## Options considered

- A. /healthz public and bodiless (200/503 only); /readyz public but bodiless; build and schema version behind require_admin.
- B. Both public with full detail.
- C. /readyz behind auth.

## Decision

**A.**

## Consequences

- Preserves the client's stated hand-debugging use while removing the version disclosure.
- Recorded explicitly: §7.7's original justification no longer holds, and the endpoint survives for a different reason — the ECS container health check of SW-ADR-071's prep-queue row.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
