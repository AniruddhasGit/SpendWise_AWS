# The cross-person adversary's brief

**One goal: make person B observe *any* data belonging to person A.**

This is the bug that ends the app. `SRC-001 §1` opens with *"Everyone sees only their own
money"* — every other defect in SpendWise is recoverable; this one is not.

**Assume the obvious paths are defended.** They are: `P-PRV-01` filters every query on the
verified identity, and row-level security filters again at the database. Attack the unusual ones.

---

## Cross-person coverage, route by route

`CROSS_PERSON_COVERAGE.tsv` beside this file maps **all 26 API routes** to the case ids that
satisfy this plan's goal — *make person B observe any data belonging to person A*. Every row is
non-empty, which is what makes Bible `E6-S3`'s second criterion auditable **as written**
(`SW-ADR-134`).

Coverage sometimes arrives under a different class label — `NEG-R-*` for the admin surface,
`NEG-T-*` for reset-token takeover, `NEG-A-*` for forged tokens. The matrix names those explicitly
rather than leaving a reader to rediscover them and conclude there is a gap.

## The rule for reading results

| Result | Verdict |
|---|---|
| `404` | **PASS** — indistinguishable from not-found, by design (`SW-ADR-050`) |
| `200` with an **empty** collection | **PASS** — the filter worked |
| `403` where a `404` was specified | **FINDING** — a 403 on an existing row is an id oracle |
| `500` | **FINDING** — an error that leaks the shape of the failure |
| **Anything containing A's data** | **SEVERITY ONE. Stop and report immediately.** |

An error *message* counts. A row *count* counts. A category *name* counts. A total that changes
when A adds an expense counts.

---

## Surfaces to attack

**Direct object references.** Every `{id}` in every path, and every id in every request body:
expenses, categories, receipts, sessions, users. Both the read verbs *and* the write verbs — a
`DELETE` that succeeds is a leak of existence even if it returns no body.

**List and filter manipulation.** `category_id` pointing at A's category · `offset` negative ·
`limit` beyond the maximum · `sort` naming a column that is not sortable · an id array · a date
range engineered to reveal counts.

**The summary endpoint.** It aggregates. A total that includes one of A's rows leaks the *amount*
without ever returning the row. Check the count, the day series, and each breakdown bucket
separately — the invariant that the breakdown sums to the total is also an oracle if one side
scopes and the other does not.

**Write paths that read.** `POST /api/expenses` carrying A's `category_id` — the foreign-key check
runs as the constraint owner and **always bypasses row-level security**, so this is a cross-person
read achieved entirely through a write. `SW-ADR-072` closes it with a composite key; verify the key
exists rather than trusting that it does.

**Receipts.** A key belonging to A's prefix, at every one of the four verbs. Possession of a key is
possession of the image, so a signed URL returned for a key you supplied is a total compromise.

**The admin surface.** Every admin endpoint, as a `user`. Then, as an admin: does any response
carry an amount, a description, or a receipt? `SW-ADR-129` makes the return type of `admin_expense_stats()` structurally
incapable of it — confirm the model, do not trust the prose.

**Error messages.** A validation error that echoes back the row it rejected. A conflict that names
the existing record. A 500 whose traceback contains a query.

**The database directly.** As the runtime role, with `app.user_id` set to B, attempt every verb
against A's rows. **This is the day-one gate and it is the only test that proves the second layer
exists.**

---

## What to do if you find nothing

**Say what you attacked and what you did not.** "I found nothing" with a thin attack log is a
failure of the review, not a success of the system.

Specifically record: which surfaces you reached, which you could not reach and why, whether you
tested the write verbs as well as the reads, and whether you went to the database or stopped at
the API. A cross-person suite that never left the API layer has not tested the layer that matters.

---

## Coverage in the case file

`SIT_NegativeCases.tsv` — **80 cases, 56 of them severity one.**

| Class | Cases |
|---|---|
| cross-person | **19** — the largest block, deliberately |
| money and time | 12 |
| role | 10 |
| auth | 9 |
| reset codes | 5 |
| storage | 5 |
| rate limits | 4 |
| injection | 3 |
| leak | 2 |
| enumeration | 1 |

Three of the cross-person cases (`NEG-X-17`, `-18`, `-19`) run **against the database as the
runtime role**, not through the API. Those are the ones that prove the second layer is real —
everything above them proves only that the first layer is working today.
