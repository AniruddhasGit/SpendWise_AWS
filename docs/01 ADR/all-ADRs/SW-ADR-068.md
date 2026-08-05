# SW-ADR-068 — Two databases inside the one RDS instance: dev and test

| Field | Value |
|---|---|
| ADR | `SW-ADR-068` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-008` · `SW-ADR-018` · `SW-ADR-009` |

## Context

The day-one evidence requires the database dropped and rebuilt from empty. Run against the single free-tier RDS instance, that destroys whatever the client was working with. But running tests against a local superuser Postgres instead would make the isolation proof worthless — superuser bypasses RLS, so the denial test would pass for the wrong reason.

## Options considered

- A. spendwise_dev and spendwise_test inside the one instance, with the same two roles in each; the test database is owned entirely by the suite.
- B. Compose Postgres for unit tests, RDS for isolation tests.
- C. One database for everything.

## Decision

**A.**

## Consequences

- Costs nothing billable, keeps RLS real for every test, and is the same pattern the prep queue already floats for DEV/UAT/PROD.
- This is a prep-queue item the client must create — owed as advance notice NOW, before the first test is written.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
