# SW-ADR-067 — The seed script lives under the test tree and never ships in the image

> **⚠ AMENDED 2026-08-05 by `SW-ADR-086` (QA FINDING-23 (LOW)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-067` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-010` · `SW-ADR-014` · `SRC-001 §6.5` |

## Context

The day-one gate requires two seeded users and four expenses summing to the agreed 75,810 paise. Nothing says what performs the seeding. If a seeder ships inside the image and is reachable in the deployed environment, it is a mechanism that creates users with known passwords on a host running plain HTTP — an unauthenticated account-creation backdoor.

## Options considered

- A. A seed script under the test tree, absent from the built image, driving the REAL registration and expense endpoints, refusing to run unless an explicit env flag is set.
- B. An Alembic data migration.
- C. Direct SQL inserts.

## Decision

**A, idempotent by design: it deletes and recreates its own two users so the expected 75,810 holds on every run.**

## Consequences

- C would skip the eight-category creation and the password-hashing path, so the gate would prove less than it claims.
- B would weld test data to the schema chain and put it in every environment.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
