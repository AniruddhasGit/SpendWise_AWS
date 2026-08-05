# SW-ADR-023 — Primary keys are BIGINT identity columns

> **⚠ LABELLED 2026-08-05 by `SW-ADR-088`, and NOT superseded.** `SW-ADR-088` marks
> this record's AWS-touching claim `UNVERIFIED — reasoned, not observed`. It replaces
> nothing. **The primary-key decision below is live authority** — see `SW-ADR-132`,
> which corrects a bookkeeping error that had withdrawn it.

| Field | Value |
|---|---|
| ADR | `SW-ADR-023` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.2` · `SRC-001 §6.6` · `SW-ADR-050` |

## Context

SRC-001 §6.2-§6.7 open every table with 'id' and never give it a type. This is the single most expensive column decision in the schema and it is unmade.

## Options considered

- A. BIGINT GENERATED ALWAYS AS IDENTITY.
- B. UUIDv4.
- C. UUIDv7 (time-ordered).

## Decision

**A. BIGINT identity on every table.**

## Consequences

- Smaller indexes and better locality than UUID on a db.t4g.micro with 20 GB and autoscaling off.
- COST, stated: ids are guessable and sequential. That is survivable ONLY because SW-ADR-050 returns a uniform 404 for not-yours-or-not-found, so enumeration yields no signal. If SW-ADR-050 is ever reversed, this ADR must be revisited in the same breath.
- Receipt keys embed a uuid4 segment (SRC-001 §8.3), so object paths stay unguessable regardless.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
