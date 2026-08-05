"""The expenses validation layer — every rule, and the collisions between them.

No database. Validation happens entirely before any query, which is what makes
this testable now and worth testing separately: a rule that fires with the wrong
sentence is a defect the database layer cannot catch.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.core.errors import ApiError, rules
from app.modules.expenses.schemas import ExpenseCreate, SummaryQuery
from app.modules.expenses.service import (
    normalise_description, validate_create, validate_summary_query,
)

AS_OF = date(2026, 8, 5)


def make(**kw) -> ExpenseCreate:
    return ExpenseCreate(**{"amount": "10.00", "spent_on": "2026-08-01", **kw})


def rule_of(exc: ApiError) -> str:
    """Recover which rule fired, from the rendered sentence. Comparing messages
    is what a client sees; comparing rule ids is what a spec states."""
    for rid, spec in rules().items():
        if spec["message"] == exc.message:
            return rid
    return f"<unmatched: {exc.message!r}>"


# ── the happy path ─────────────────────────────────────────────────────────
def test_a_valid_body_yields_paise_and_description() -> None:
    paise, desc = validate_create(make(amount="1250.00", description="Auto"), as_of=AS_OF)
    assert paise == 125000
    assert desc == "Auto"


def test_forged_fields_are_discarded_before_validation_not_rejected() -> None:
    """`SW-ADR-130` / `NEG-X-10`: a forged `user_id` yields **201**, not 422.

    `extra="ignore"` is what makes that possible, and it is the reason
    `extra="forbid"` is unavailable no matter how tempting it looks.
    """
    body = ExpenseCreate.model_validate({
        "amount": "10.00", "spent_on": "2026-08-01",
        "user_id": 99, "id": 4242, "amount_paise": 1, "currency": "USD",
    })
    assert not hasattr(body, "user_id")
    paise, _ = validate_create(body, as_of=AS_OF)
    assert paise == 1000       # from `amount`, never from the forged amount_paise


# ── description ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("raw", ["", "   ", "\t\n ", None])
def test_blank_descriptions_become_null(raw: str | None) -> None:
    assert normalise_description(raw) is None


def test_a_non_empty_description_is_stored_verbatim_never_trimmed() -> None:
    """`CV-22`. `SW-ADR-115` says normalised to null, not stripped — trimming
    would silently alter what the person typed."""
    assert normalise_description("  chai  ") == "  chai  "


def test_501_characters_is_rejected_naming_description() -> None:
    with pytest.raises(ApiError) as e:
        validate_create(make(description="x" * 501), as_of=AS_OF)
    assert e.value.field == "description"
    assert rule_of(e.value) == "description.length"


def test_500_characters_is_accepted() -> None:
    _, desc = validate_create(make(description="x" * 500), as_of=AS_OF)
    assert desc is not None and len(desc) == 500


# ── spent_on ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("day", ["2026-08-05", "2016-08-05", "2027-08-05", "2026-12-31"])
def test_dates_inside_the_window_are_accepted(day: str) -> None:
    validate_create(make(spent_on=day), as_of=AS_OF)


@pytest.mark.parametrize("day", ["2016-08-04", "2027-08-06", "2062-01-01", "2001-01-01"])
def test_dates_outside_the_window_are_rejected_naming_spent_on(day: str) -> None:
    with pytest.raises(ApiError) as e:
        validate_create(make(spent_on=day), as_of=AS_OF)
    assert e.value.field == "spent_on"
    assert rule_of(e.value) == "spent_on.window"


def test_the_window_boundary_uses_calendar_arithmetic_not_day_counts() -> None:
    """`CV-23`. Ten calendar years before 2026-08-05 is 2016-08-05 — not
    2016-08-07, which is what 3652 days would give across two leap years."""
    validate_create(make(spent_on="2016-08-05"), as_of=AS_OF)
    with pytest.raises(ApiError):
        validate_create(make(spent_on="2016-08-04"), as_of=AS_OF)


def test_leap_day_clamps_rather_than_drifting() -> None:
    """29 February minus ten years has no 29th to land on. `relativedelta`
    clamps to the 28th; a naive subtraction would produce 1 March."""
    validate_create(make(spent_on="2016-02-29"), as_of=date(2026, 2, 28))


# ── collisions: the reason precedence exists ───────────────────────────────
def test_a_bad_amount_beats_a_bad_date() -> None:
    """`amount.grammar` (3rd) outranks `spent_on.window` (6th)."""
    with pytest.raises(ApiError) as e:
        validate_create(make(amount="abc", spent_on="2062-01-01"), as_of=AS_OF)
    assert e.value.field == "amount"
    assert rule_of(e.value) == "amount.grammar"


def test_scale_beats_the_date_and_returns_the_sentence_the_prd_quotes() -> None:
    """`12.345` must return *"Amount must have at most two decimal places."* —
    not the grammar sentence. That distinction is why the grammar pattern checks
    shape and the scale rule counts places."""
    with pytest.raises(ApiError) as e:
        validate_create(make(amount="12.345", spent_on="2062-01-01"), as_of=AS_OF)
    assert rule_of(e.value) == "amount.scale"
    assert e.value.message == "Amount must have at most two decimal places."


def test_three_broken_rules_still_report_exactly_one() -> None:
    with pytest.raises(ApiError) as e:
        validate_create(make(amount="0", spent_on="2062-01-01", description="x" * 501),
                        as_of=AS_OF)
    assert e.value.field == "amount"
    assert rule_of(e.value) == "amount.bounds"


# ── the summary's query pair ───────────────────────────────────────────────
def q(**kw) -> SummaryQuery:
    return SummaryQuery.model_validate({"from": "2026-08-01", "to": "2026-08-31", **kw})


def test_a_valid_range_passes() -> None:
    validate_summary_query(q())


def test_an_inverted_range_names_to() -> None:
    with pytest.raises(ApiError) as e:
        validate_summary_query(q(**{"from": "2026-08-31", "to": "2026-08-01"}))
    assert e.value.field == "to"
    assert rule_of(e.value) == "range.order"


def test_400_days_is_accepted_and_401_is_not() -> None:
    """The cap is on `(to - from).days + 1` — the number of `by_day` rows —
    because both ends are inclusive (`SW-ADR-085`). Off by one here would put
    the boundary exactly where the only test sits."""
    validate_summary_query(q(**{"from": "2026-01-01", "to": "2027-02-04"}))   # 400
    with pytest.raises(ApiError) as e:
        validate_summary_query(q(**{"from": "2026-01-01", "to": "2027-02-05"}))  # 401
    assert rule_of(e.value) == "range.span"
    assert "400" in e.value.message, "the message must NAME the cap (SIT-E2-S7-02)"


def test_a_range_before_2000_names_from() -> None:
    with pytest.raises(ApiError) as e:
        validate_summary_query(q(**{"from": "1999-12-31", "to": "2000-01-01"}))
    assert e.value.field == "from"
    assert rule_of(e.value) == "range.floor"


def test_span_outranks_floor_when_both_are_broken() -> None:
    """`?from=1999-01-01&to=2026-08-31` breaks both. The contract says span."""
    with pytest.raises(ApiError) as e:
        validate_summary_query(q(**{"from": "1999-01-01", "to": "2026-08-31"}))
    assert rule_of(e.value) == "range.span"


def test_both_filters_at_once_is_refused_naming_uncategorised() -> None:
    with pytest.raises(ApiError) as e:
        validate_summary_query(q(category_id=3, uncategorised=True))
    assert e.value.field == "uncategorised"
    assert rule_of(e.value) == "filter.exclusive"


def test_uncategorised_false_alongside_a_category_is_fine() -> None:
    """`false` is treated as absent — "cannot both be **given**" (`CV-02`)."""
    validate_summary_query(q(category_id=3, uncategorised=False))
