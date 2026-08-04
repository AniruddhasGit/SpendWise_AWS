# SW-ADR-019 — Alembic takes a Postgres advisory lock explicitly

| Field | Value |
|---|---|
| ADR | `SW-ADR-019` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S11.6` · `SRC-001 E-4` · `Decided under SW-ADR-015` |

## Context

SRC-001 S11.6 states 'Alembic takes an advisory lock, so two tasks booting at once is safe.' This is FALSE. Alembic acquires no advisory lock automatically. Partial serialisation comes from the alembic_version row lock inside the migration transaction, but the race is real and known.

## Options considered

- A. Take pg_advisory_xact_lock explicitly in env.py.
- B. Move migrations out of container start into a separate one-off task.

## Decision

**A. The lock is taken explicitly. Migrations remain at container start, per SRC-001 S11.6's intent.**

## Consequences

- Corrects a load-bearing premise the client stated as settled fact. A premise inherited without checking is a bug with a long fuse.
- B remains the better practice at larger scale and is recorded as a fast-follow, not a v1 requirement.
- Filed as ERRATUM E-4 against SRC-001.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
