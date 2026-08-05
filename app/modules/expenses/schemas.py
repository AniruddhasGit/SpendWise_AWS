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
