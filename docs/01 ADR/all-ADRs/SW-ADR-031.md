# SW-ADR-031 — The audit log is immutable at the database level

> **⚠ AMENDED 2026-08-05 by `SW-ADR-083` (QA FINDING-18 (MEDIUM)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-031` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.7` · `SRC-001 §6.9` · `SRC-001 §10.8` |

## Context

SRC-001 §6.9 says the audit log survives user deletion, and §10.8 requires a row per admin action. Nothing prevents an UPDATE or DELETE against it.

## Options considered

- A. REVOKE UPDATE, DELETE on admin_audit_log from every application role.
- B. A trigger that raises on UPDATE/DELETE.
- C. Application discipline.

## Decision

**A and B together: the grant is revoked, and a trigger raises so the refusal is visible rather than a silent permission error.**

## Consequences

- An append-only claim that only the application enforces is not append-only.
- Consequence: the table can never be pruned by the app. Growth is accepted and tracked under OPEN-PRUNE-01.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
