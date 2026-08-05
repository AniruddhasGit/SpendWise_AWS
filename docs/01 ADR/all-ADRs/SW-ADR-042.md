# SW-ADR-042 — The users table sits outside RLS, deliberately and in writing

> **⚠ NOT CURRENT AUTHORITY.** The ledger records this record as `RETIRED`. The text
> below is history — for status trust the ledger (Art XI.1).

> **⚠ WITHDRAWN 2026-08-05 by `SW-ADR-090`.** This ruling waived a quality check, which
> Art IX.6 reserves to the client. The question is now `OPEN-USERSRLS-01`. The analysis
> below stands; the decision does not.

| Field | Value |
|---|---|
| ADR | `SW-ADR-042` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **RETIRED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.5` · `SW-ADR-018` |

## Context

Login must read a user row by email BEFORE any verified user id exists, so a policy keyed on the per-request GUC either errors or matches nothing and login can never succeed. SW-ADR-018 never addressed the unauthenticated case.

## Options considered

- A. users carries no RLS; isolation on it is the application layer plus require_admin.
- B. A policy permitting a single-row read when the GUC is unset.
- C. A separate pre-auth role.

## Decision

**A, with the reasoning recorded here rather than left as an unexplained omission.**

## Consequences

- STATED PLAINLY: the one table holding every email and password hash is outside the database-layer guarantee. That is a real reduction in the SW-ADR-018 promise and it is written down, not hidden.
- It also preserves SRC-001 §10.5's timing defence, which requires the lookup to be ALLOWED to return nothing rather than to error.
- Compensating: password_hash is never selected into any response model; the users repository exposes no method that returns it outside the auth service.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
