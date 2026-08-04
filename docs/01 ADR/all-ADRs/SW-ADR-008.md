# SW-ADR-008 — One RDS instance from day one

| Field | Value |
|---|---|
| ADR | `SW-ADR-008` |
| Pack | `SPENDWISE_V1` |
| Type | MONEY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §9` |

## Context

The build could run against local Postgres in Docker and move to RDS later, or against real RDS immediately. Local is faster to iterate; RDS surfaces the three places they differ - no superuser, forced SSL, restricted extensions - in week one instead of a bad week later.

## Options considered

- A. Local Docker Postgres now, one RDS for DEV later - RECOMMENDED by the build session.
- B. One RDS instance from day one, used as DEV.
- C. Local only until the app is finished.

## Decision

**B. The build happens against real RDS. This AMENDS SW-ADR-004.**

## Consequences

- RECORDED AS AN OVERTURN, not smoothed into agreement. The recommendation was A; the ruling is B. The build session's own stated kill condition applied - 'if practising AWS matters more than shipping SpendWise, work against real RDS from day one' - and the client confirmed that is the case.
- COST: the inner loop slows; every migration is a network round-trip, and the day-one proof requires migrate-up, down, up again cleanly.
- CONSTRAINT: the free tier covers roughly 750 instance-hours a month against ~730 hours in a month. That is ONE always-on instance. DEV + UAT + PROD as three live instances is roughly 3x over.
- UNVERIFIED: AWS moved to a credit-based free tier for new signups in 2025. The build session does not know which model this account is on and has not checked. That is a money matter reserved to the client.
- BLOCKING: the day-one proof cannot start until an RDS instance and its two database roles exist.

## Supersedes

`SW-ADR-004` — see that record for the position it replaced.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
