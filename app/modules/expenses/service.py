"""`expenses.service` — translates between HTTP shapes and rows.

The only layer permitted to call another module's service (`SW-ADR-017`'s
sanctioned crossing): the expenses *repository* returns `category_id` and
totals; this service asks the categories service for names. One round trip for
the browser — which is what `SRC-001` asked for. It asked for one request, not
one SQL statement.

Everything in this module below `validate_create` is **pure**, and so is tested
without a database. The parts that touch one live in `repository.py`.
"""
from __future__ import annotations

from datetime import date

from app.core.clock import days_elapsed, span_days, spent_on_window
from app.core.errors import Violation, validation_error
from app.core.money import AmountError, parse_amount
from app.modules.expenses.schemas import ExpenseCreate, SummaryQuery

MAX_DESCRIPTION = 500
MAX_SPAN_DAYS = 400                       # SW-ADR-118
RANGE_FLOOR = date(2000, 1, 1)            # SW-ADR-118


def normalise_description(raw: str | None) -> str | None:
    """Whitespace-only becomes `None`; anything else is stored **verbatim**.

    `SW-ADR-115` says *normalised to null*, not *stripped*. Trimming a non-empty
    description would silently alter what the person typed, which `SW-ADR-112`
    refuses to do for amounts — the same argument applies here (`CV-22`).
    """
    if raw is None or not raw.strip():
        return None
    return raw


def validate_create(body: ExpenseCreate, *, as_of: date) -> tuple[int, str | None]:
    """-> `(amount_paise, description)` or raise the ONE winning violation.

    Rules are collected and then ranked, rather than raised where they are
    found. Raising on the first *discovered* problem would make the answer
    depend on the order this function happens to check things — and the whole
    point of `error_codes.precedence` is that the order is the contract's, not
    the implementation's.

    `category_id` ownership is deliberately **not** checked here. The composite
    foreign key enforces it at the database, so a pre-read would be a second
    source of truth that can disagree — and would race (`SW-ADR-072`).
    """
    violations: list[Violation] = []

    paise = 0
    try:
        paise = parse_amount(body.amount)
    except AmountError as exc:
        violations.append(Violation(exc.rule, "amount"))

    floor, ceiling = spent_on_window(as_of)
    if not (floor <= body.spent_on <= ceiling):
        violations.append(Violation("spent_on.window", "spent_on"))

    description = normalise_description(body.description)
    if description is not None and len(description) > MAX_DESCRIPTION:
        violations.append(Violation("description.length", "description"))

    if violations:
        raise validation_error(violations)
    return paise, description


def validate_summary_query(q: SummaryQuery) -> None:
    """The five rules that fire only on the summary's query pair.

    Collected then ranked, for the same reason as above. `range.span` outranks
    `range.floor`, so `?from=1999-01-01&to=2026-08-31` reports the 400-day cap
    rather than the floor — both are true and the contract picks one.
    """
    violations: list[Violation] = []

    if q.category_id is not None and q.uncategorised:
        violations.append(Violation("filter.exclusive", "uncategorised"))
    if q.to < q.from_:
        violations.append(Violation("range.order", "to"))
    elif span_days(q.from_, q.to) > MAX_SPAN_DAYS:
        # `elif`: an inverted range has a negative span, and reporting the cap
        # for it would be a true statement about a meaningless number.
        violations.append(Violation("range.span", "to"))
    if q.from_ < RANGE_FLOOR:
        violations.append(Violation("range.floor", "from"))

    if violations:
        raise validation_error(violations)


def elapsed_for(q: SummaryQuery, *, as_of: date) -> int:
    """The divisor. **Days, not rows** — and capped at today, so a range running
    into the future does not inflate the denominator and deflate the average."""
    return days_elapsed(q.from_, q.to, as_of)
