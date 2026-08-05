# SW-ADR-149 — `SECURITY DEFINER` is not a bypass: three admin capabilities that silently did nothing

| Field | Value |
|---|---|
| ADR | `SW-ADR-149` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | `SW-ADR-129` (the mechanism, not the ruling) |
| Raised by | GOAL_15 M4 implementation — the admin dashboard reported 0 expenses for every account but the caller's |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-06 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §4.2` · `SW-ADR-081` · `SW-ADR-100` · `SW-ADR-106` · `SW-ADR-129` · `SW-ADR-136` |

## Context

Three capabilities the permission matrix grants an administrator were **implemented, tested by
eye, and did nothing**:

| `SRC-001 §4.2` grants | what actually happened |
|---|---|
| count another person's expenses | `(0, NULL)` for every account but the caller's |
| see who is currently signed in | an empty list, reading as "nobody is signed in" |
| force sign someone out | `UPDATE` matched zero rows and **reported success** |

Every one of them failed the same way, and it is the way this system fails when it fails:
**`FORCE ROW LEVEL SECURITY` applies to the table owner too.**

`SW-ADR-081` chose that deliberately — an owner who can quietly bypass their own policies is a
migration away from an isolation hole. But `SECURITY DEFINER` only changes *which role* the
function runs as. It does not exempt that role from policies, and the policies key on
`app.user_id`, which is still the **caller's**. So the definer function ran as the owner and saw
exactly what the admin could already see.

`admin_expense_stats` had been written, generated, migrated and shipped in that state.

The force-sign-out is the worst of the three: `UPDATE … WHERE user_id = <someone else>` matches
nothing under RLS and raises nothing. The endpoint returned 200, the audit log recorded
*"signed user #2 out of 0 session(s)"*, and the session stayed live.

## Decision

**A. The definer functions swap `app.user_id` to their target and restore it.**
`set_config(…, is_local => true)` — transaction-local, restored before returning, and the
function **refuses to run when the GUC is unset** rather than restoring to a state that was never
there. An unset GUC reads as `NULL`; an empty one raises on `::bigint`; the two are not the same,
and quietly converting one into the other is how a later query fails for a reason nobody can trace.

`LANGUAGE plpgsql`, `VOLATILE` — not `STABLE`. It mutates a GUC, and labelling that `STABLE`
would be a lie the planner is entitled to act on.

**B. Two more functions, and the return type stays the guard.**

* `admin_user_sessions(target)` — `RETURNS TABLE` declaring **no `ip` and no `user_agent`**, which
  makes `SW-ADR-106` structurally true at the DATABASE and not merely in a Pydantic model.
* `admin_revoke_sessions(target)` — `RETURNS TABLE (revoked BIGINT)`, so the count is the
  function's, not a `rowcount` that reports zero as success.

**C. No new policy, and no new GUC that grants breadth.** A policy on `sessions` keyed on an
`app.admin_scan`-style flag would work and would be wrong twice over: the runtime role can set any
GUC it likes, so it is not a second line of defence; and a policy has no column dimension, which
is precisely why `SW-ADR-129` replaced one with a function in the first place.

**D. A cross-user session list is assembled PER USER**, by walking the account page — the same
shape `stats_for` already had. There is deliberately no query in this system that returns every
person's sessions at once.

**E. The unauthenticated reset path sets the identity it has just proved.**
`POST /api/auth/reset/complete` has no auth dependency by design, so `app.user_id` was unset and
its session revocation matched zero rows — leaving every session of a possibly-compromised account
live while the response said the reset succeeded. It now calls `set_request_identity` from the
redeemed token's row: possession of the token *is* the proof of identity this endpoint accepts,
and it has just been checked.

## Consequences

- **Three capabilities that returned a plausible answer.** Not an error, not a 500 — `0`,
  `[]`, and `200 OK`. An admin dashboard would have shown "0 expenses" for every account and
  looked like a correct, privacy-respecting product.
- `SW-ADR-129`'s *ruling* is untouched and is now actually enforced: counting is separated from
  reading, and the bypass is bounded by a two-column signature.
- **The general shape, for the next person:** in this system, a privilege you cannot exercise
  fails **silently and successfully**. RLS does not raise; it filters. Every capability that
  crosses a person boundary needs a test that asserts a *non-empty, non-zero* result for a
  **different** user — asserting the shape of the response proves nothing, because the shape is
  correct.
- `tools/apply_function.py` exists because the baseline migration is already stamped in both
  databases. It extracts the blocks from the GENERATED `security.sql` rather than carrying its own
  copy, so what is deployed and what is specified cannot differ.

---

*Ruled under `SW-ADR-015`.*
