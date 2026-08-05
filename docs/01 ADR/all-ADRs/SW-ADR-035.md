# SW-ADR-035 — A composite foreign key enforces that an expense's category belongs to its owner

> **⚠ AMENDED 2026-08-05 by `SW-ADR-072` (QA FINDING-3 (CRITICAL)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-035` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.6` · `SRC-001 §7.3` · `SW-ADR-018` · `SW-ADR-017` |

## Context

Nothing requires that `expenses.category_id` points at a category owned by the same user. Postgres foreign-key checks run as the constraint owner and ALWAYS bypass row-level security, so RLS cannot catch this — an insert carrying another user's category_id succeeds, and the summary's category breakdown then either renders another user's category name into the attacker's dashboard or silently drops the row and reports a wrong total.

## Options considered

- A. UNIQUE (id, user_id) on categories, and expenses references (category_id, user_id) as a composite FK.
- B. A service-layer ownership check on every write.
- C. Accept it.

## Decision

**A. The database enforces it.**

## Consequences

- This is a cross-user read achieved entirely through a write path, and it is invisible to the day-one gate as written.
- B was rejected as the sole control precisely because it is the single-forgotten-check failure SW-ADR-018 exists to prevent — but it is added as well, so both layers hold.
- Costs one extra unique index on categories.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
