# CR-001 — the contract every worker builds to

Frozen before any parallel work started, so four workers cannot disagree about
a field name. **If this file and your instinct differ, this file wins.**

---

## 1. Schema

One new column, one new function.

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ NULL;
CREATE INDEX ix_users_deleted_at__where_deleted_at_is_null
    ON users (deleted_at) WHERE deleted_at IS NULL;
```

The unique index on `lower(email)` stays **total**. A soft-deleted account keeps its address.

```sql
CREATE OR REPLACE FUNCTION admin_user_daily(
        target_user_id BIGINT, from_date DATE, to_date DATE)
    RETURNS TABLE (day DATE, total_paise BIGINT, entries BIGINT)
```

`SECURITY DEFINER`, `plpgsql`, `VOLATILE`, `SET search_path = pg_catalog, public`, and it swaps
`app.user_id` to the target and restores it — **exactly like `admin_expense_stats`**, including
refusing to run when the GUC is unset. See `SW-ADR-149`: without the swap it silently returns
nothing for every account but the caller's.

**THREE COLUMNS AND NO FOURTH.** No `category_id`, no `description`, no expense id. That is the
line CR-001 draws, and the return type is what enforces it.

---

## 2. API

### `DELETE /api/auth/me` — soft-delete your own account

* 204, no body. Clears the session cookie.
* Sets `deleted_at = now()` **and** `is_active = false`, revokes every session, all in one
  transaction.
* The **last active administrator** cannot do this: `409 CONFLICT`, `field: "is_active"`.
* Every row the person owns is untouched — expenses, categories, the person record.
* `POST /api/auth/deactivate` **stays**, and stays distinct. Deactivate is "pause me"; delete is
  "close it". Both are reversible by an administrator; only one of them says so on the tin.

### Sign-in and sessions

* A deleted account is refused at login with the **same generic 401** as a wrong password
  (`SESSION_INVALID`) — `SW-ADR-100 (1)`, unchanged.
* An in-flight session is refused by `principal_for` with `ACCOUNT_DEACTIVATED`.
* `UserRepository.by_email` and `.by_id` return the row; the **service** decides. Do not filter
  deleted rows out of the repository — the admin needs them.

### `GET /api/admin/users/{user_id}/spending?from=&to=`

The new one. `require_admin`, on the router, as always.

Response — `AdminUserSpending`:

```json
{
  "user": { "id": 2, "display_name": "…", "email": "…", "is_active": true, "deleted": false },
  "from": "2026-08-01",
  "to": "2026-08-31",
  "total_paise": 379049,
  "total": "3790.49",
  "count": 4,
  "days_elapsed": 5,
  "daily_average_paise": 75810,
  "daily_average": "758.10",
  "by_day": [ { "date": "2026-08-01", "total_paise": 125000, "count": 1 }, … ]
}
```

* **NO `by_category`. NO descriptions. NO expense rows.** A reviewer should be able to grep this
  model for `categor` and find nothing.
* Every day in the range appears, including zeroes — same as the person's own summary.
* Range rules are the SAME as `/api/expenses/summary`: `range.required`, `range.order`,
  `range.span` (400 days), `range.floor` (2000-01-01). Reuse `validate_summary_query`.
* `days_elapsed` and the half-up average use the SAME helpers as the person's summary
  (`app/core/clock.py`, `app/core/money.py`). Do not reimplement the rounding.
* Writes **one** `users_list_viewed` audit row. The nine-item allowlist is closed; a tenth action
  is a migration and this change does not need one.

### `GET /api/admin/users` — additions

* Response rows gain **`deleted: boolean`** (derived from `deleted_at is not None`).
* Query gains `deleted=true|false` to filter. Default: **deleted accounts are included**, because
  an administrator looking for someone who has left must be able to find them.
* `POST /api/admin/users/{id}/active` with `is_active: true` on a deleted account **also clears
  `deleted_at`** — restoring is one action, not two.

---

## 3. Client

### Settings

* A **Delete my account** control, alongside the existing Deactivate.
* Two-step confirm. The copy must say what actually happens: the account closes, sign-in is
  refused, **the records are retained and an administrator can restore it**, and the email address
  stays taken. Offer the export first.
* Never label it "Delete" and call `/deactivate`, or vice versa.

### Admin

* The accounts table gains a **View** action opening a per-person detail pane.
* The detail pane shows: who they are, status, `expense_count`, `last_activity`, live sessions —
  and the **line plot of their spending over the selected range**, with the total, the count and
  the daily average.
* A **time filter**: This month · Last month · Last 30 days · Last 90 days · This year. Reuse
  `PERIODS` from `lib/period.js` and extend it there rather than duplicating.
* **No category chart, no donut, no ribbon, no entry list on this pane.** If you find yourself
  reaching for `Donut` here, re-read CR-001.
* Deleted accounts show a clear `deleted` status and a **Restore** action.

---

## 4. Non-negotiables that did not change

* Money is integer paise. The client never divides by 100.
* Every colour is a token; `npm run lint:tokens` fails on a raw hex.
* Targets are ≥44×44 at phone width. Nothing overflows 375px.
* The day-one gate still computes 75810 with `APP_TODAY_OVERRIDE=2026-08-05`.
* The audit row and the change it records commit together or neither does.


---

## 5. Addenda — questions this contract left open

Added after the fact, because the record-keeping worker read this file adversarially and found
four things it did not answer. Each is decided here rather than left to whichever worker reached
it first, which is how two halves of one feature come to disagree.

### 5.1 Superseding `SW-ADR-107` breaks live citations — a warning this file owed its workers

Flipping a record to SUPERSEDED makes `consistency_check.py`'s `adr-status` check fail every file
that still rests authority on it. Four citations were in flight when it landed. **If you cite
`SW-ADR-107`, put historical framing in the same paragraph** — "superseded by `SW-ADR-150`", "no
longer", "previously". The checker looks for exactly that vocabulary, and it is right to: a
citation of a dead record with no acknowledgement that it is dead is indistinguishable from one
written before it died.

The same rule applies to the day-one value. A wrong figure such as `75809` (truncation) or
`94762` (dividing by the row count) may appear **only on a line that also says it is wrong** —
"not", "never", "truncated", "instead of". The LINE, not the paragraph: a warning two sentences
away excuses nothing.

This paragraph failed that check on its first draft, which is the best demonstration of it
available. The two figures sat on one line and the words "they are wrong" wrapped onto the next,
so the checker saw a bare assertion of the truncated value in a document about the day-one gate —
and it was right to. Each figure now carries its own disqualifier on its own line.

### 5.2 A closed account is not a paused one, and the overview must stop conflating them

`AdminRepository.account_counts` derives `deactivated = total - active`, so a closed account is
counted as a paused one. That was fine when closing did not exist.

**Decision:** `AdminOverview` gains `accounts_deleted`, and `accounts_deactivated` becomes
*paused but not closed* — `total - active - deleted`. Three numbers that sum to the total, because
two numbers that overlap is how a dashboard comes to report more deactivations than it has
accounts.

### 5.3 Restore

* `is_active: true` against a closed account clears `deleted_at` **and** sets `is_active` — one
  action, because two would mean an account that is un-deleted and still refused, and nothing on
  the screen would explain the difference.
* `is_active: false` against a closed account clears **nothing**. It is already inactive; the
  request is a no-op that must not resurrect the account by implication.
* **The last-administrator guard does not apply to restore.** It exists to stop the count of
  active administrators reaching zero; restoring can only raise it. A guard that fired here would
  block the recovery it was written to protect.

### 5.4 "Every row the person owns is untouched" — except the sessions

§2 says the person's rows are untouched two lines after requiring every session to be revoked, and
sessions are rows the person owns. The precise statement: **every row that records what they did
survives; every row that grants access is revoked.** That distinction is the whole of soft
deletion, and it is worth stating in those terms rather than by listing tables.
