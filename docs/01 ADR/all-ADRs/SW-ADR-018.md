# SW-ADR-018 — Per-user isolation is enforced twice: in the application and by Postgres row-level security

> **⚠ AMENDED 2026-08-05 by `SW-ADR-082` (QA FINDING-17 (MEDIUM)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-018` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S10.2` · `Decided under SW-ADR-015` |

## Context

SRC-001 S10.2 requires every query to filter on the user id from the verified token. That is application-layer isolation only. One endpoint that forgets the filter leaks another person's money, and a controller-only check is the classic false green. The day-one gate requires the denial to hold at the DATABASE layer.

## Options considered

- A. Add Postgres RLS properly: two database roles, FORCE ROW LEVEL SECURITY, SET LOCAL per request.
- B. Application-layer filtering only, formally waiving the database-layer gate.
- C. Application filtering plus RLS on the expenses table alone.

## Decision

**A. Both layers. Decided by the build session under SW-ADR-015.**

## Consequences

- Adopting the STRICTER option is not a waiver, so this did not require the client's signature. Option B would have been a waiver of a quality check and is reserved to the client.
- TWO DATABASE ROLES: a migration/owner role that creates the schema, and a runtime role that does NOT own the tables, is NOT superuser, and does NOT hold BYPASSRLS.
- FORCE ROW LEVEL SECURITY on every protected table - a table's owner bypasses RLS otherwise, silently.
- The session dependency issues SET LOCAL for the verified user id inside the request transaction.
- VERIFIED BY QUERYING THE CATALOG, never assumed. And RED-PROOFED: the policy is disabled on purpose, the denial test is watched going red, then reverted and the revert verified.
- Building against local superuser Postgres would make this proof worthless - superuser bypasses everything, so the test would pass or fail for the wrong reason. SW-ADR-008 removes that risk.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
