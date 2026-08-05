# SW-ADR-061 — Migration failure is fast, loud, and bounded

| Field | Value |
|---|---|
| ADR | `SW-ADR-061` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §11.6` · `SW-ADR-019` |

## Context

Nothing says what happens when a migration fails partway through a multi-revision upgrade, or when the database is unreachable at boot. pg_advisory_xact_lock is the BLOCKING variant, so a second task waits forever rather than failing — and if the client has stopped the RDS instance to conserve free-tier hours, an option the prep queue explicitly offers, every task hangs indefinitely.

## Options considered

- A. No retry; exit non-zero; one structured ERROR naming the revision reached versus head; lock_timeout and statement_timeout set on the migration connection.
- B. Bounded retry with backoff for connection failures only.

## Decision

**A, plus: the current and target revision are printed on EVERY boot whether or not a migration runs.**

## Consequences

- An indefinite silent hang is otherwise the DEFAULT failure mode.
- Printing revisions unconditionally means the log answers 'what schema is this task on' without a database query.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
