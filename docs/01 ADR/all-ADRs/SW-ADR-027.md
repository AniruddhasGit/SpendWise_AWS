# SW-ADR-027 — Case-insensitive email via a unique index on lower(email)

| Field | Value |
|---|---|
| ADR | `SW-ADR-027` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.2` · `SW-ADR-018` |

## Context

SRC-001 §6.2 requires email to be 'unique, case insensitive' and does not say how, nor whether the user's original capitalisation survives.

## Options considered

- A. `CREATE UNIQUE INDEX ON users (lower(email))`, storing the original casing.
- B. The citext extension.
- C. Lowercase on write.

## Decision

**A. A functional unique index; the column stores exactly what the user typed.**

## Consequences

- B was rejected because citext requires a CREATE EXTENSION that the restricted runtime role of SW-ADR-018 cannot perform, and RDS extension availability is unverified by this session.
- C was rejected because it destroys information for display with no gain.
- Every lookup must therefore query `lower(email) = lower(:input)` or the index is not used.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
