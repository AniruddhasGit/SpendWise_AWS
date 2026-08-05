# SW-ADR-071 — Password reset completion works: `password_resets` leaves RLS

| Field | Value |
|---|---|
| ADR | `SW-ADR-071` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-041` |
| Raised by | QA FINDING-1 (CRITICAL) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-041` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-041` put `password_resets` behind a policy keyed on the verified user id. Completing a reset is **unauthenticated by definition** — the user is locked out, which is the entire reason the admin role exists (`SRC-001 §1`). With the GUC unset the lookup matches nothing and the update is denied, so account recovery is dead. `SW-ADR-042` identified this exact class of problem for `users` and solved it only there.

## Decision

**`password_resets` carries NO row-level security, for the same reason and with the same written justification as `users` in `SW-ADR-042`. The isolation that matters is enforced in the application: a token is looked up by its hash, which is 32 bytes of urandom, and the row is single-use.**

## Consequences

- Removes `password_resets` from `SW-ADR-041`'s protected list. That list is now: expenses, categories, sessions.
- The admin *issue* path and the user *complete* path both work, which they could not before.
- STATED PLAINLY: this is a second table outside the database-layer guarantee. Both this and `SW-ADR-042` are consequences of one root cause — RLS keyed on a request-scoped user id cannot serve any pre-authentication path. That root cause is now named rather than patched twice.
- `SW-ADR-032`'s unique index on `token_hash` is what makes application-layer lookup safe: a token resolves to exactly one row or none.

---

*A superseding record, not an edit. `SW-ADR-041` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
