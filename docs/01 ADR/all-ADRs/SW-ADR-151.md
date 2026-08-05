# SW-ADR-151 — An administrator may see HOW MUCH over time, and still not WHAT ON: the return type moves, the mechanism does not

| Field | Value |
|---|---|
| ADR | `SW-ADR-151` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | `SW-ADR-129` (the line the return type is pointed at, not the mechanism) |
| Raised by | `CR-001`, the client, 2026-08-06: *"they can see the expenses that are happening not the categories spent on so the will be able to see the line plot for that particular user"* |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-06 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CR-001` · `SRC-001 §4.2` · `SRC-001 §4.5` · `SW-ADR-081` · `SW-ADR-129` · `SW-ADR-136` · `SW-ADR-149` |

## Context

**This record reverses a clause of `SRC-001 §4.2`, at the client's instruction.** It is the top of
the authority order in `CONSTITUTION.md` Art II.1, it is the client's own permission matrix in
their own words, and the row being reversed is this one:

> | | user | admin |
> |---|---|---|
> | See anyone else's expense amounts | no | **no** (see §4.5) |

The bold **no** in the admin column was the client's, not an inference, and it was not decoration:
`SW-ADR-129` built the entire admin data path around it. When a row-level policy turned out to have
no column dimension and therefore could not express "aggregate only", `SW-ADR-129` replaced it with
a `SECURITY DEFINER` function whose `RETURNS TABLE (expense_count, last_activity)` made an amount
**unable to come back at all** — *"A function has a return type; a policy does not."*

`CR-001` moves that line. The client's sentence, verbatim, is where the new line sits:

> they can see **the expenses that are happening not the categories spent on** so the will be able
> to see the line plot for that particular user and have the filter option to see the line plot
> based on time filter.

`SRC-001` is a frozen input (Art II.2) and cannot be edited where it stands, and its fingerprint in
`docs/00 SourceOfTruth/fingerprints.json` makes an edit a build failure rather than a judgement
call. `CR-001` is the record of the instruction; this ADR is the record of the decision. Art II.6
requires that the reversal be marked, and marking it is what this section is.

## Decision

**A. `admin_user_daily(target_user_id, from_date, to_date)` returns THREE columns, and no fourth.**

```sql
RETURNS TABLE (day DATE, total_paise BIGINT, entries BIGINT)
```

`day`, `total_paise`, `entries`. There is **no `category_id`, no `description`, no expense id**, and
that absence is the whole design. Category and description stay unreadable **structurally** — not
absent from a response model, not filtered by a service, but impossible to express through the
function an administrator is granted. A caller cannot ask this function what somebody spent their
money *on*, at any granularity, because PostgreSQL has nowhere to put the answer.

That is precisely `SW-ADR-129`'s mechanism, unchanged, pointed at a line that moved. `SW-ADR-129`
ruled that the *return type* is the guard because it is the only construct available that can make
"aggregate only" structurally true; the client has since decided that the aggregate may include an
amount. **A principle pointed at a new line is not a principle abandoned** — and the test of that
claim is that the mechanism got no weaker: the previous ruling made *amount* unanswerable, this one
makes *category and description* unanswerable, and both by the same construct.

The alternative would have been to return expense rows and let the API layer drop the columns the
client did not grant. Every response would have looked identical. It would also have meant a query
authorised to read descriptions, one field-list edit away from returning them, with nothing below
the Python layer to stop it — which is the exact shape `SW-ADR-129` was written to eliminate, and
`SW-ADR-129` records that **no stated test would have caught it**, because every test asserts on
the response shape and the response shape would have been right.

**B. It inherits `SW-ADR-149`'s GUC swap, and cannot work without it.**

`SECURITY DEFINER` is not a bypass. `SW-ADR-081` chose `FORCE ROW LEVEL SECURITY`, which applies to
the table owner too, so a definer function running as the owner is still filtered by policies keyed
on `app.user_id` — **still the caller's**. Without the swap this function returns an empty set for
every account except the administrator's own, and returns it **silently**: no error, no zero-row
warning, just a line plot that is flat at zero and looks like a person who has not spent anything.

So it does exactly what `admin_expense_stats` does after `SW-ADR-149`: `set_config('app.user_id',
target, is_local => true)` for the length of the query, restored before returning, and it
**refuses to run when the GUC is unset** rather than restoring to a state that was never there.
`LANGUAGE plpgsql`, `VOLATILE` — it mutates a GUC, and `STABLE` would be a lie the planner is
entitled to act on. `SET search_path = pg_catalog, public` is mandatory, because a definer function
without one is a privilege-escalation vector.

`SW-ADR-149`'s closing warning is the acceptance criterion for this function and is not optional
here: a privilege you cannot exercise fails **silently and successfully** in this system, so the
test that proves this works must assert a **non-empty, non-zero** result for a **different** user.
Asserting the response shape proves nothing, because the shape is correct either way.

**C. Every read is audited.**

`GET /api/admin/users/{user_id}/spending` writes one `users_list_viewed` row naming the target,
inside the same transaction as the read — `SW-ADR-083`'s append-only log, and the audit row and the
thing it records commit together or neither does. A capability that lets one person see another
person's money must leave a trace that the person can be shown; an unaudited read of this is worse
than the read.

It reuses the existing action rather than inventing a tenth: the `CHECK` constraint's list of
actions is closed, a new value is a migration, and this is a read of the account list from the
administrator's side. That is a deliberate, cheap answer and it has a cost — the audit sentence for
a spending view and for an account-list view are the same sentence, distinguishable only by the
`details` payload and the target id. Named here so that whoever needs the distinction knows it was
seen and priced, not missed.

**D. The response carries no category surface, anywhere.**

`AdminUserSpending` reports the person, the range, the total, the count, the days elapsed, the
daily average and `by_day`. It carries **no `by_category`, no descriptions, no expense rows** — a
reviewer should be able to search the model for `categor` and find nothing. Every day in the range
appears including the zeroes, the range rules are the ones `/api/expenses/summary` already
enforces, and the average uses the same half-up integer helper. Reimplementing the rounding here
would produce a second answer to a question that already has one.

The client-side pane inherits the same restriction: a line plot over time, a total, a count and an
average. **No donut, no category ribbon, no entry list** — the visual affordances that exist
elsewhere in this product are the ones this record exists to withhold.

## Consequences

- **This is a reduction in privacy that was previously ruled out. It is stated plainly and it is
  not softened.** An administrator can now see how much a named person spends, day by day, over any
  range they choose. `SRC-001 §4.2` said no, `SRC-001 §4.5` was the stated value behind it,
  `SW-ADR-129` made it true at the database, and the client has now instructed otherwise. The
  decision is theirs to make and it was made deliberately. Recording it in the softer form — "the
  administrator gains a reporting view" — would be the same document set that spent `SW-ADR-129`
  refusing to let a privacy claim be true only in a response model, letting one be false only in a
  sentence nobody reads.
- **What did not move.** Category and description remain unreadable by an administrator at every
  layer: no policy on `expenses` or `categories` consults `app.is_admin` (`SW-ADR-129`, restoring
  `SW-ADR-043`), the GUC still has no consumer, and the two definer functions an administrator can
  reach between them expose a count, a last-activity date, a daily total and a daily entry count.
  The line `CR-001` draws is *"the expenses that are happening not the categories spent on"*, and
  it is drawn in a `RETURNS TABLE` clause.
- **`SW-ADR-129`'s ruling is amended in scope, not in method,** and its text stays where it is with
  a banner pointing here — Art III.2. A reader arriving at `SW-ADR-129` must not conclude that
  amounts are unreachable by an administrator; they must conclude that whatever is unreachable is
  unreachable *because there is no column for it*, and then come here for the current column list.
- **The next request of this shape has an obvious cheap answer, and it is the wrong one.** Adding a
  fourth column to this function is a one-line change that no test in this repository would fail.
  The three-column signature is the only thing standing between "see how much" and "see everything",
  and it is load-bearing in exactly the way a line of SQL does not look. Any request to widen it is
  a change request against `CR-001` and a new record here, not a patch.

---

*Ruled under `SW-ADR-015`.*
