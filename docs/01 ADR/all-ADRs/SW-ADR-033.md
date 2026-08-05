# SW-ADR-033 — Category names are unique per user, case-insensitively

| Field | Value |
|---|---|
| ADR | `SW-ADR-033` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.5` · `SRC-001 §9.2` |

## Context

SRC-001 §6.5 gives each user their own category set but does not say whether two categories may share a name.

## Options considered

- A. UNIQUE (user_id, lower(name)).
- B. No constraint.
- C. Case-sensitive uniqueness.

## Decision

**A.**

## Consequences

- Two categories named 'Food' and 'food' produce two bands in the ribbon that a user cannot tell apart, and SRC-001 §9.2 makes the ribbon the primary filter control.
- Consequence: renaming a category can now fail with a conflict, which needs an error path — covered by SW-ADR-051's envelope.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
