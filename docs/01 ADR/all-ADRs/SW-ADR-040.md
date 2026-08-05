# SW-ADR-040 — SQLAlchemy MetaData naming convention

| Field | Value |
|---|---|
| ADR | `SW-ADR-040` |
| Pack | `SPENDWISE_V1` |
| Type | TECHNICAL_STANDARD |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §2.1` |

## Context

Without an explicit convention, Alembic autogenerate emits unnamed constraints, and a later migration cannot drop what it cannot name.

## Options considered

- A. Set a naming_convention on MetaData covering ix/uq/ck/fk/pk.
- B. Leave defaults.

## Decision

**A. The standard five-key convention, set before the first migration is generated.**

## Consequences

- Set this after the first migration exists and every later constraint is inconsistent with the first. It is nearly free now and expensive to retrofit.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
