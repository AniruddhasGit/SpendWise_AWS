# SW-ADR-038 — Pagination, default sort, and the tiebreak

| Field | Value |
|---|---|
| ADR | `SW-ADR-038` |
| Pack | `SPENDWISE_V1` |
| Type | API_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §7.3` · `SRC-001 §7.6` · `SRC-001 §6.8` |

## Context

No list endpoint in SRC-001 §7 states a page size, a sort, or what happens when two rows share a date. `spent_on` is a DATE with no time component, so same-day entries — the common case — have no defined order and Postgres may return them differently on two identical requests.

## Options considered

- A. Limit/offset with a default and a maximum, and an explicit ORDER BY with a total tiebreak.
- B. Cursor pagination.
- C. Return everything.

## Decision

**A. `limit` default 50, maximum 200; `offset` default 0; every list returns `{items, total, limit, offset}`. Expenses sort `spent_on DESC, created_at DESC, id DESC`. Admin user list sorts `created_at DESC, id DESC`.**

## Consequences

- The id tiebreak is what makes the sort total — without it, pagination over an unstable order duplicates and skips rows, and in a money list a duplicated row is visibly counted twice while the SUM-derived total does not move.
- Cursor pagination is better at scale and unnecessary at this one; recorded as fast-follow.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
