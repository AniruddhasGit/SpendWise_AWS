# SW-ADR-082 — The request-scoped user id is set with `set_config`, never `SET LOCAL`

| Field | Value |
|---|---|
| ADR | `SW-ADR-082` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-018` |
| Raised by | QA FINDING-17 (MEDIUM) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-018` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

Every RLS ADR says the user id reaches the policy via `SET LOCAL`. PostgreSQL's `SET` accepts only literals — it cannot take a bind parameter — so a literal implementation requires interpolating a value into SQL **on every authenticated request**. Art IV.8 and `SRC-001 §10.3` forbid exactly that. The two rules collided on the hottest path in the application.

## Decision

**`text("SELECT set_config('app.user_id', :uid, true)")` with a bound parameter. `SET LOCAL` is never used with an interpolated value anywhere in this codebase.**

## Consequences

- Removes the only forced Art IV.8 violation in the design, at a cost of one line.
- The `true` third argument makes it transaction-local, which is what `SET LOCAL` was there to provide.

---

*A superseding record, not an edit. `SW-ADR-018` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
