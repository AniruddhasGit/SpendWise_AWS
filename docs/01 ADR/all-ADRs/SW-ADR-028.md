# SW-ADR-028 — Enumerated columns are VARCHAR + CHECK, never native Postgres ENUM

| Field | Value |
|---|---|
| ADR | `SW-ADR-028` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.2` · `SRC-001 §6.7` |

## Context

SRC-001 §6.2 (role), §6.6/§6.2 (currency) and §6.7 (action) are enumerations with no stated representation.

## Options considered

- A. TEXT + a CHECK constraint listing the permitted values.
- B. Native Postgres ENUM types.
- C. Unconstrained TEXT.

## Decision

**A. TEXT + CHECK.**

## Consequences

- Native ENUMs cannot have a value removed and cannot be altered inside a transaction in older Postgres — a migration hazard on a schema that will change often during a learning build.
- C was rejected: an unconstrained role column is a privilege bug waiting for a typo.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
