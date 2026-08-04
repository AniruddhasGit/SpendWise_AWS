# SW-ADR-004 — Spend posture: all spend blocked

| Field | Value |
|---|---|
| ADR | `SW-ADR-004` |
| Pack | `SPENDWISE_V1` |
| Type | MONEY |
| Decision status | **SUPERSEDED** |
| Decision outcome | SUPERSEDED_BY_SW-ADR-008 |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | DO_NOT_RELEASE |
| Release status | WITHDRAWN |
| Sources | `SRC-002 §5` |

## Context

Before any billable resource is created, the money-signer must state what may be spent without a further signature. Money is a reserved matter; no model may decide it at any confidence.

## Options considered

- A. Nothing yet - local development and free tiers only.
- B. A named small monthly ceiling.
- C. Approval sought for each individual spend.

## Decision

**A. All spend blocked. Local development and free tiers only.**

## Consequences

- SUPERSEDED one hour later by SW-ADR-008, which authorised one RDS instance from day one.
- Retained unedited and marked, not rewritten. An amended decision that quietly changes its own text is how a project loses the ability to explain itself.

## Superseded by

`SW-ADR-008`. This record is retained unedited as history.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
