# SW-ADR-011 — The Dockerfile is written late, not during the day-one proof

| Field | Value |
|---|---|
| ADR | `SW-ADR-011` |
| Pack | `SPENDWISE_V1` |
| Type | DELIVERY_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S11.1` · `SRC-002 §12` |

## Context

SRC-001 S11.1 specifies a multi-stage Dockerfile. Whether it exists at the day-one proof determines what 'clean clone' evidence is available at that point.

## Options considered

- A. Dockerfile written as part of the day-one proof.
- B. Dockerfile written by the build session, but only once the app is otherwise ready.

## Decision

**B. The build session writes it, late.**

## Consequences

- The clean-clone evidence WEAKENS and is labelled weaker - see SW-ADR-009's four-line ladder.
- Follows from SW-ADR-008: the day-one proof runs against RDS, so no local database container is needed to execute it.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
