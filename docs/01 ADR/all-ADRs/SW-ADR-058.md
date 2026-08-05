# SW-ADR-058 — No optimistic UI for expenses

| Field | Value |
|---|---|
| ADR | `SW-ADR-058` |
| Pack | `SPENDWISE_V1` |
| Type | UX_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-010` · `SRC-001 §9.2` · `SRC-001 §6.6` |

## Context

Nothing says whether a new expense appears before the server confirms it. The choice is not free here: the ribbon, day bars, subtotals and daily average all come from the summary endpoint, computed server-side under SW-ADR-010's rule. Optimistic insertion means re-deriving that rule in JavaScript — a second implementation of the one business rule the day-one gate checks.

## Options considered

- A. Wait for 201, then refetch the summary; the panel shows a pending state.
- B. Optimistically insert into the list only.
- C. Full optimistic update including aggregates.

## Decision

**A.**

## Consequences

- SW-ADR-010's rule must have exactly one implementation. C creates a drift bug the gate cannot catch.
- B leaves the totals visibly disagreeing with the list beneath them, in a money app.
- Also: submit and delete controls disable on first click. SRC-001 §6.6 has no uniqueness constraint, so two identical POSTs create two indistinguishable rows and the user's total silently doubles.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
