"""Wire shapes for the expenses module.

Derived from `docs/03 PRD/api/contract.json` — `request_models.ExpenseCreate`,
`models.Expense`, `models.Summary`. Where this file and the contract disagree,
**the contract wins**, and `test_schemas_match_the_contract.py` fails first.

Two decisions here look like Pydantic trivia and are neither:

* **`extra="ignore"`, model-wide.** A forged `user_id` in the body is discarded
  *before validation*, never rejected — `NEG-X-10` requires **201** with the row
  owned by the caller, so `extra="forbid"` is not available (`SW-ADR-130`).
* **`amount` is `Any`, not `str`.** A JSON *number* must return
  `amount.grammar`, not `field.type` (`CV-21`). Typing it `str` would make
  Pydantic reject the number first, with the wrong rule and the wrong sentence.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import Violation, validation_error

# The ONE permitted coercion, applied per field (`request_models.parsing`).
# `strict=True` on the model blocks ISO-8601 text -> date as well as everything
# else, and JSON has no date type - so a strict `date` field can never be
# populated from a JSON body. This annotation carves out exactly that one case
# and nothing more: a quoted integer is still `field.type`.
IsoDate = Annotated[date, Field(strict=False)]

# Everything the client may send that the server derives for itself. Discarded
# before validation — listed here so the set is reviewable rather than implied
# by whatever the model happens not to declare.
DISCARDED = ("user_id", "id", "amount_paise", "currency",
             "created_at", "updated_at", "receipt_key", "category_name")


class ExpenseCreate(BaseModel):
    """`POST /api/expenses`.

    `strict=True`: a quoted integer (`{"category_id": "9"}`) is `field.type`,
    not a silent coercion to 9 (`request_models.parsing`). The one permitted
    coercion is ISO-8601 text to `date` — see `IsoDate` above, which carves it
    out per field. It has to be explicit: `strict=True` blocks that conversion
    too, and since JSON has no date type, a strict `date` field could never be
    populated from a request body at all.
    """

    model_config = ConfigDict(extra="ignore", strict=True)

    # `Any`, deliberately. The grammar check owns every non-conforming amount.
    amount: Any
    spent_on: IsoDate
    category_id: int | None = None
    description: str | None = None


class ExpenseUpdate(BaseModel):
    """`PATCH /api/expenses/{expense_id}`. Every field optional; at least one
    must be present, checked in the service so the message can name `body`."""

    model_config = ConfigDict(extra="ignore", strict=True)

    amount: Any = None
    spent_on: IsoDate | None = None
    category_id: int | None = None
    description: str | None = None


class ExpenseOut(BaseModel):
    """The response shape. Both `amount` and `amount_paise` are returned.

    Not redundancy: the client never divides by 100 (a float bug waiting to
    happen), and a test can assert on the exact integer. `category_name` is
    `null` when `category_id` is null — the `Uncategorised` label belongs to
    `CategoryBucket` alone, and putting it here would make a synthetic display
    string indistinguishable from a real category name (`SW-ADR-141 D`).
    """

    id: int
    user_id: int
    category_id: int | None
    category_name: str | None
    amount: str
    amount_paise: int
    currency: str
    description: str | None
    spent_on: date
    receipt_key: str | None
    created_at: datetime
    updated_at: datetime | None


class CategoryBucket(BaseModel):
    category_id: int | None
    category_name: str
    color: str
    total_paise: int
    count: int
    percent: int


class DayBucket(BaseModel):
    date: date
    total_paise: int
    count: int


class Summary(BaseModel):
    """`GET /api/expenses/summary`.

    `daily_average_paise` is `int | None` — **`None`, never `0`, when
    `days_elapsed` is 0**. A wholly future range has no average, and `0` reads
    as "spent nothing" on the first screen every new user sees (`SW-ADR-053`).
    """

    model_config = ConfigDict(populate_by_name=True)

    from_: Annotated[date, Field(alias="from")]
    to: date
    total_paise: int
    total: str
    count: int
    days_elapsed: int
    daily_average_paise: int | None
    daily_average: str | None
    by_category: list[CategoryBucket]
    by_day: list[DayBucket]


class SummaryQuery(BaseModel):
    """The summary's query parameters.

    Five of the fourteen validation rules fire only here, and the precedence
    tie-break resolves same-class collisions by **this model's declaration
    order** — so the order below is contract, not style (`CV-13`).
    """

    model_config = ConfigDict(extra="ignore", strict=True, populate_by_name=True)

    from_: Annotated[date, Field(alias="from", strict=False)]
    to: IsoDate
    category_id: int | None = None
    # `false` is treated as absent; mutually exclusive with `category_id`,
    # checked in the service so the message can name `uncategorised` (`CV-02`).
    uncategorised: bool = False


def require_range(from_: str | None, to: str | None) -> None:
    """`range.required`. Raises unless BOTH ends of the range were supplied.

    The contract puts this rule ahead of every other range rule and names the
    failure mode it exists to prevent (`error_codes.precedence.scope`):

        A missing `from` or `to` is `range.required`, with `field` set to the
        key that is actually missing — **not** `field.required`, which would
        otherwise make `range.required` unreachable (G2).

    That is precisely what happened. Both routes annotated `from` and `to` as
    REQUIRED query parameters, so FastAPI refused the request before any rule in
    this system ran and every caller received `field.required`. The rule was
    written, generated into the error tables, given a message and a tie-break —
    and could not fire. **A rule that cannot fire is the same defect as a
    missing one**, which is why the contract calls the condition out by name
    rather than leaving it to be noticed.

    An EMPTY value counts as missing. `?from=&to=…` is a supplied key with
    nothing in it; treated as present it reaches the date parser and reports
    `field.type`, telling the caller their date is malformed when what they
    actually did was omit it — two different problems with two different fixes.

    `from` wins when BOTH are absent, because `§6.1`'s worked request writes
    `?from=…&to=…` in that order. A request with no parameters at all is the
    most likely malformed one there is, and leaving it to a 50/50 choice is the
    thing the precedence block exists to end.

    ONE helper, called by both routes. `CR-001 §2` requires the administrator's
    range rules and the person's own to be the same rules through the same
    helper — and the pre-existing test asserted only that the two endpoints
    AGREE, which they did while both were wrong. Two copies of this check would
    pass that test forever.
    """
    missing = not (from_ or "").strip(), not (to or "").strip()
    if not any(missing):
        return
    raise validation_error([Violation("range.required", "from" if missing[0] else "to")])


class ExpensePage(BaseModel):
    """`P-REC-02`. `total` here is a ROW COUNT, not a money total — the money
    total lives on `Summary` as `total_paise`, and confusing the two is the kind
    of mistake that reads fine in code review."""

    items: list[ExpenseOut]
    total: int
    limit: int
    offset: int
