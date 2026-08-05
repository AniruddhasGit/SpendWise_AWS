# SW-ADR-136 — The token carries `sub`, and `set_config` runs before the session lookup

| Field | Value |
|---|---|
| ADR | `SW-ADR-136` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice run 2, GUESS #1 / CONTRADICTION C9 (BLOCKING) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §5.2` · `SW-ADR-022` · `SW-ADR-082` · `SW-ADR-097` · `03_security_isolation.md` |

## Context

`03_security_isolation.md` orders authentication: verify the signature → `SELECT session WHERE
id = jti` → check revocation and expiry → `set_config('app.user_id', …)` → query.

**That order cannot work, and the failure is total.** `security.sql` puts `FORCE ROW LEVEL
SECURITY` on `sessions` with `USING (user_id = current_setting('app.user_id', true)::bigint)`.
At the moment of the session lookup the GUC is unset, so `current_setting(…, true)` returns
`NULL`, the predicate evaluates to `NULL` rather than true, and **the lookup returns zero rows for
every request ever made**. Authentication as specified never succeeds.

Worse, the GUC cannot be set from what the token carries. `SRC-001 §5.2` and `SW-ADR-022` name
only `jti`; `SW-ADR-099` adds `exp`. **No document states a claim holding the user id**, so there
is nothing to put in `set_config` before the row that would have told you the user id is readable.
It is a genuine bootstrap deadlock, not an ordering preference.

Two cold readers reached the same conclusion independently and both had to invent a claim name to
proceed.

## Decision

**A. The token carries `sub`, the `users.id` of the principal, as a string.** The full claim set
is `sub`, `jti`, `iat`, `exp` — closed; an unlisted claim is ignored, never trusted.

**B. `set_config('app.user_id', :uid, true)` is the FIRST statement of the request transaction**,
issued from `sub` before any ORM query, including the session lookup. Bound parameter, never
`SET LOCAL` (`SW-ADR-082`).

**C. The session lookup then runs under the policy**, and the service asserts
`session.user_id == sub`. A forged `sub` scopes the attacker to their own rows and the `jti` will
not be found there — so the forgery fails closed, and `sub` is never trusted as authorisation on
its own. **It selects a scope; the session row grants the access.**

**D. One `AsyncSession`, one transaction, per request.** `set_config(…, true)` is
transaction-local: if any repository opens a second transaction the GUC is gone and every query
silently returns **zero rows** rather than erroring. That is the worst failure shape in this
system — an empty dashboard that looks like an honest empty state.

## Consequences

- **`FORCE ROW LEVEL SECURITY` stays on `sessions`.** Removing it would be waiving a quality
  check, which Art IX.6 reserves to the client. This decision needs no signature because it
  adopts the stricter arrangement, not a weaker one.
- No schema change. `sub` is a token claim, not a column.
- `03_security_isolation.md`'s sequence is corrected; the diagram was the artifact that made the
  order look considered.
- **A `GOTCHAS.md` entry**, because the second-transaction failure is silent: an empty result is
  indistinguishable from a person with no expenses.
