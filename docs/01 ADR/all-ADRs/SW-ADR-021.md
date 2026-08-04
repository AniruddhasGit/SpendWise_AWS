# SW-ADR-021 — The first-admin claim is gated on BOOTSTRAP_ADMIN_EMAIL

| Field | Value |
|---|---|
| ADR | `SW-ADR-021` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S4.4` · `SRC-001 E-2` · `Decided under SW-ADR-015` |

## Context

SRC-001 S4.4 says the first account created in a fresh database becomes an admin. On a freshly deployed instance that means whoever finds the URL first becomes administrator of the system.

## Options considered

- A. Gate the claim on a BOOTSTRAP_ADMIN_EMAIL environment variable.
- B. Seed an admin via migration or CLI.
- C. Accept the race and register immediately after deploying.

## Decision

**A. Only the address named in BOOTSTRAP_ADMIN_EMAIL can claim the first-admin slot.**

## Consequences

- Keeps the client's intent - self-serve, no separate seeding step - while closing the window.
- Unchanged from SRC-001 S4.4: after the first, only an existing admin promotes anyone, and an admin cannot demote themselves if they are the last one.
- Filed as ERRATUM E-2 against SRC-001.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
