# SW-ADR-129 — An admin sees expense counts through a SECURITY DEFINER function, never a policy

> **⚠ AMENDED 2026-08-06 by `SW-ADR-149`.**
> The ruling below stands — counting is separated from reading, and the return type is the
> guard. What changed is that it did not WORK: `SECURITY DEFINER` runs as the owner, and
> `FORCE ROW LEVEL SECURITY` subjects the owner to its own policies, so the function saw only
> the caller's rows and returned `(0, NULL)` for every other account. `SW-ADR-149` makes the
> mechanism match the decision.

> **⚠ AMENDED 2026-08-06 by `SW-ADR-151`.**
> The mechanism below is untouched and is now used twice: the *return type* is the guard,
> because a function has one and a policy does not. What moved is the line it is pointed at.
> `CR-001` reversed `SRC-001 §4.2`'s admin row at the client's instruction, so an
> administrator may now see a daily **total** through `admin_user_daily` — and still no
> category and no description, because there is no column for either. Do not read this
> record as "an admin cannot see an amount"; read it as "an admin can only see what the
> signature declares", and come to `SW-ADR-151` for the current signature.

| Field | Value |
|---|---|
| ADR | `SW-ADR-129` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-077` (and closes the `SW-ADR-043` contradiction) |
| Raised by | GOAL_13 uncoached slice, GUESS #6 (BLOCKING) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-043` · `SW-ADR-077` · `SRC-001 §4.5` · the GOAL_13 uncoached vertical slice, 2026-08-05 |

## Context

Two APPROVED records contradicted each other and the authority order cannot separate them. `SW-ADR-043`: the admin GUC is consulted **only** by the policies on `sessions` and `password_resets`, and *deliberately NOT* by those on `expenses` — "admins CANNOT read expenses or categories at the database layer at all." `SW-ADR-077`: `expenses` gains a policy "consulted only when `app.is_admin` is set", permitting *aggregate reads only*.

**The generated `security.sql` implemented `SW-ADR-077`, and it is worse than the contradiction.** A PostgreSQL row-level security policy is exactly that — **row**-level. It has no column dimension. `FOR SELECT USING (current_setting('app.is_admin') = 'true')` is an unqualified permissive policy, OR'd with the owner policy, that returns **every column of every row** — amount and description included.

So `SW-ADR-077`'s decision was **not implementable in the form it specified**, and shipping it would have made `SRC-001 §4.5` — the client's stated privacy value — false at the database, while `P-PRV-02` claimed it was "structurally true". **No stated test would have caught it**, because every test asserts on the API response shape, and the API would have kept returning the right fields from a query that was allowed to read everything.

## Decision

****`expenses` carries NO admin policy.** `SW-ADR-043`'s position is restored: the admin GUC is never consulted by a policy on `expenses` or `categories`.

The admin count comes from a `SECURITY DEFINER` function owned by `spendwise_owner`:

```sql
CREATE FUNCTION admin_expense_stats(target BIGINT)
    RETURNS TABLE (expense_count BIGINT, last_activity DATE)
    LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
        SELECT count(*), max(spent_on) FROM expenses WHERE user_id = target;
    $$;
REVOKE ALL ON FUNCTION admin_expense_stats(BIGINT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION admin_expense_stats(BIGINT) TO spendwise_app;
```

**`app.is_admin` is never set on a request-scoped connection — and as this pack now stands, it is never set at all.**

`SW-ADR-043` reserved the GUC for policies on `sessions` and `password_resets`. Neither exists: `P-PRV-02`'s matrix gives `sessions` **no admin policy**, and `password_resets` sits **outside RLS entirely** (`SW-ADR-071`). So the GUC has no consumer anywhere in `security.sql`, which states exactly that.

*(Corrected 2026-08-05, raised by the second uncoached slice as contradiction C8: the first draft of this record described the reservation as though those two policies were live. The record that closed an isolation hole was itself wrong about the shape of the fix.)***

## Consequences

- **A function has a return type; a policy does not.** `RETURNS TABLE (expense_count, last_activity)` is the only construct in PostgreSQL that can make "aggregate only" structurally true. An amount cannot come back through it because there is no column for one.
- `SECURITY DEFINER` bypasses row security by design — which is exactly why the *return type* must be the guard rather than the policy. `SET search_path` is mandatory: without it, a definer function is a privilege-escalation vector.
- The admin service calls the function. It never issues a `SELECT` against `expenses`, so `SRC-001 §3.4`'s module rule holds unchanged.
- **`permissions.tsv` was right and the SQL was wrong.** It already said `admin | expenses | aggregate read only`; the implementation could not deliver that shape.
- `SW-ADR-043`'s per-table policy matrix must still be published in the PRD. It was ruled and never written — carried forward, not closed here.

---

*A superseding record, not an edit. The superseded text stays in place with a banner
pointing here — Art III.2.*
