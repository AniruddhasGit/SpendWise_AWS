"""`admin.schemas` — account administration; reads ONE amount, deliberately.

**E4-S2 is enforced here and asserted by introspection**: no model in this file
declares a field capable of holding an amount or a description. That is not a
convention — `test_admin_models_cannot_carry_money` walks these classes and
fails on a field whose name or type could hold one.

`SRC-001 §4.2`, the client's own permission matrix:

> | | user | admin |
> | See anyone else's expense amounts | no | **no** |

The bold **no** is theirs. An admin manages accounts; the money stays private
from everyone, including the person who can deactivate the account holding it.

---

**`CR-001` MOVED THAT LINE, and the introspection test has not caught up yet.**

The client raised `CR-001` on 2026-08-06 and reversed their own **no**: an
administrator opening a person's detail pane may now see *how much* that person
spent over a range, as a total, a count, a daily average and a line plot. The
change request says so plainly, and says plainly that it is a reduction in
privacy taken on purpose.

So the paragraph above is no longer true of this whole module, and it is left
standing because it is still true of **every model in it but one**:

* `AdminUserSpending` — and `SpendingDay`, which exists only as its `by_day`
  rows — are the sole carriers of an amount here. Nothing else gained a field,
  and nothing else may.
* What `CR-001` did **not** grant is the more important half, and it did not
  move at all: *"the expenses that are happening **not the categories spent
  on**"*. There is no `by_category` on `AdminUserSpending`, no description, no
  expense row, no category id — at any granularity. A reviewer should be able to
  grep this file for `categor` and find nothing.
* That line is held **structurally**, not by this file's good behaviour. The new
  `admin_user_daily()` function's `RETURNS TABLE` clause declares `day`,
  `total_paise` and `entries`, and there is no fourth column for a category to
  arrive in — the same mechanism `SW-ADR-129` built, pointed at the line the
  client has moved rather than abandoned.

`tests/test_admin.py::test_no_admin_response_model_can_hold_an_amount_or_a_description`
still asserts the OLD rule and therefore fails on `total_paise` and
`daily_average_paise`. **That failure is the test being out of date, not this
module being wrong**, and the fix belongs in the test: it should assert that
`AdminUserSpending` and `SpendingDay` are the *only* models carrying money —
which is a stronger guarantee than the one it makes today, because today a field
named exactly `total` is on its allowlist as a row count and would sail through
on any model at all. The test owner holds that change; do not weaken it here,
and do not add a money field to a second model to make it pass.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(extra="ignore", strict=True)


class AdminUser(BaseModel):
    """`P-ADM-01`. Two derived fields and no third.

    `expense_count` and `last_activity` come from `admin_expense_stats()`, a
    `SECURITY DEFINER` function whose `RETURNS TABLE` clause declares exactly
    those two columns (`SW-ADR-129`). "How much" is not answerable **from here**
    at any layer — not by this model, not by that function, not by a policy.
    `CR-001` answers it on `AdminUserSpending` and only there.

    `deleted` is a **boolean derived from `users.deleted_at`**, not the timestamp
    (`CR-001`, `SW-ADR-150`). The instant an account closed is an operational
    detail the account list has no use for, and the same reasoning `SW-ADR-106`
    applied to `ip` applies here: a field that does not exist cannot be leaked by
    a handler that forgets. It is a THIRD state, not a rename of `is_active` —
    an account can be paused (`is_active false`, `deleted false`) or closed
    (both), and the client's status column and Restore action need to tell them
    apart.
    """

    id: int
    email: str
    display_name: str
    role: str
    is_active: bool
    deleted: bool
    created_at: datetime
    expense_count: int
    last_activity: date | None


class AdminUserPage(BaseModel):
    items: list[AdminUser]
    total: int
    limit: int
    offset: int


class SpendingDay(BaseModel):
    """One calendar day of one person's spending. **Three fields and no fourth.**

    The shape mirrors `expenses.schemas.DayBucket` exactly, because it is the
    same day on the same line plot seen by a different reader — and two shapes
    for one concept is how a client ends up with two chart components that
    disagree at the boundary.

    There is no `category_id` here and there is nowhere to put one: the row
    arrives from `admin_user_daily()`, whose `RETURNS TABLE` declares `day`,
    `total_paise` and `entries`. The database is what makes that true; this
    model merely does not undo it.
    """

    date: date
    total_paise: int
    count: int


class AdminUserSpending(BaseModel):
    """`CR-001`, `SW-ADR-151`. **The one model in this module that holds money.**

    An administrator opening a person's detail pane sees how much they spent
    over a range, and how it moved day by day. That was ruled out by
    `SRC-001 §4.2` and the client reversed it themselves; the reversal is
    recorded in `docs/15 ChangeRequest/CR-001_*`, and every read of this response
    writes an audit row.

    What is deliberately absent is the whole design, and it is easier to state as
    a list of things a reviewer should fail this file for containing: a
    `by_category`, a description, an expense id, a `spent_on`, a category name, a
    "top merchant". The client drew the line at *"the expenses that are happening
    not the categories spent on"*, and a total plus a daily series is exactly one
    side of it.

    Every field below is the SAME name and the SAME meaning as on
    `expenses.schemas.Summary`, minus `by_category`. Not a coincidence and not
    laziness: the numbers are produced by the same helpers (`core.clock`,
    `core.money`), so if the person's own dashboard and the administrator's view
    of it ever disagreed about a total, that would be a defect worth finding
    fast — and identical names are what make the comparison a one-line test
    rather than a translation exercise.

    `daily_average_paise` is `int | None` — **`None`, never `0`, when
    `days_elapsed` is 0** (`SW-ADR-053`). A range wholly in the future has no
    average, and `0` reads as "this person spent nothing", which about a real
    account is not a rounding difference but a false statement.

    `from_` carries `alias="from"` because `from` is a Python keyword; the wire
    name is `from`, as it is on the person's own summary.
    """

    model_config = ConfigDict(populate_by_name=True)

    # The whole account row, not a hand-picked subset. `CR-001 §3` wants the
    # detail pane to show who they are, their status, `expense_count` and
    # `last_activity` beside the plot — all of which `AdminUser` already carries
    # — and a narrower `SpendingUser` here would be a second definition of "who
    # is this" that the two views could drift apart on.
    user: AdminUser
    from_: Annotated[date, Field(alias="from")]
    to: date
    total_paise: int
    total: str
    count: int
    days_elapsed: int
    daily_average_paise: int | None
    daily_average: str | None
    by_day: list[SpendingDay]


class AdminSession(BaseModel):
    """`P-ADM-02`. **No `ip` and no `user_agent`** (`SW-ADR-106`, `NEG-R-10`).

    "Who is signed in" is an operational question. Answering it does not
    require handing an administrator a location history, and the fields simply
    do not exist on the model — so no handler can leak them by forgetting.
    """

    id: int
    user_id: int
    issued_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class AdminSessionPage(BaseModel):
    items: list[AdminSession]
    total: int
    limit: int
    offset: int


class AuditRow(BaseModel):
    """One audited action.

    `sentence` is rendered SERVER-SIDE (`P-ADM-08`): the audit view shows a
    formatted line, never raw JSON. A client assembling the sentence would
    have to know all nine action types, and would silently print `[object
    Object]` for the tenth.
    """

    id: int
    admin_id: int
    action: str
    target_user_id: int | None
    created_at: datetime
    sentence: str


class AuditPage(BaseModel):
    items: list[AuditRow]
    total: int
    limit: int
    offset: int


class ActiveRequest(BaseModel):
    model_config = STRICT
    is_active: bool


class RoleRequest(BaseModel):
    model_config = STRICT
    role: Literal["user", "admin"]


class ResetToken(BaseModel):
    """`P-ADM-04`. Shown ONCE.

    The database stores only `token_hash`; this is the only moment the token
    exists in the clear anywhere, and it is never logged (`SW-ADR-032`).
    """

    token: str
    expires_at: datetime


class DayCount(BaseModel):
    date: date
    count: int


class AdminOverview(BaseModel):
    """The admin dashboard's headline figures.

    Every number here counts **accounts, sessions or actions**. There is no
    money on this model and there is no way to derive any: `expenses_recorded`
    is a count of rows summed from `admin_expense_stats()`, which returns no
    amount to sum.
    """

    accounts_total: int
    accounts_active: int
    # PAUSED but not closed, and `accounts_deleted` is closed. The three sum to
    # `accounts_total`; before `CR-001` they were two figures that overlapped,
    # because closing an account sets `is_active = false` as well and a closed
    # account was therefore reported as a paused one (`CR-001 §5.2`).
    accounts_deactivated: int
    accounts_deleted: int
    admins: int
    sessions_live: int
    expenses_recorded: int
    accounts_active_last_7_days: int
    accounts_dormant_30_days: int
    accounts_never_used: int
    signups: list[DayCount]
    audit_last_7_days: int
