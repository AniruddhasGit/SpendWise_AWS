# SW-ADR-026 — String column types and lengths

> **⚠ AMENDED 2026-08-05 by `SW-ADR-084` (QA FINDING-21 (LOW)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-026` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.2` · `SRC-001 §6.6` · `SRC-001 §10.10` |

## Context

Not one character column in SRC-001 §6 has a stated type or length. Postgres TEXT and VARCHAR(n) perform identically, so the only question is where the limit is enforced and whether it is discoverable.

## Options considered

- A. TEXT in Postgres with a CHECK constraint on length, and the same bound in Pydantic.
- B. VARCHAR(n).
- C. TEXT with no bound.

## Decision

**A. TEXT + CHECK, mirrored by a Pydantic constraint, so the limit is enforced twice and stated once.**

## Consequences

- Bounds set: email 254, display_name 100, category name 50, expense description 500, user_agent 500, receipt_key 512, audit action 50.
- C was rejected: an unbounded description is a cheap way to fill 20 GB of free-tier storage.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
