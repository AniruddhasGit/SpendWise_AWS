"""The day-one gate's arithmetic, proved without a database.

`docs/06 DataModel/seed/expected_summary.json` is the complete gate payload,
computed from `contract.json` by the documentation generator. This module feeds
the same fixture through the **application's** functions and asserts the two
agree, field for field.

That is a real proof of a real thing, and it is worth being precise about what
it is not. It proves the arithmetic — the total, the divisor, the rounding, the
ordering, the percentages, the day series. It does **not** prove the database
returns the right rows to compute it from; that is `E0-S7` and `E0-S9`, and both
need an RDS instance. Two failures, deliberately separated: right rows, and
right maths on them.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.core.money import (
    AmountError, daily_average, half_up, largest_remainder, parse_amount, to_display,
)
from app.modules.expenses.summary import (
    CategoryTotal, DayTotal, build_by_category, build_by_day, build_summary,
)

REPO = Path(__file__).resolve().parents[1]
EXPECTED = json.loads(
    (REPO / "docs" / "06 DataModel" / "seed" / "expected_summary.json").read_text("utf-8"))
CONTRACT = json.loads(
    (REPO / "docs" / "03 PRD" / "api" / "contract.json").read_text("utf-8"))

FIXTURE = CONTRACT["seed_fixture"]["expenses_by_person"]["A"]
CATEGORIES = {c["id"]: (c["name"], c["color"]) for c in CONTRACT["categories"]["seeded"]}


# ── the number the whole project rests on ──────────────────────────────────
def test_the_gate_value_is_75810() -> None:
    """`379049` paise over `5` elapsed days, rounded half-up, is **75810**.

    Not 75809 (truncation) and not 94762 (dividing by the row count). Both are
    named in the contract as the wrong answers because both look plausible.
    """
    assert daily_average(379049, 5).daily_average_paise == 75810


def test_the_gate_value_is_not_the_two_named_wrong_answers() -> None:
    wrong = CONTRACT["gate"]["wrong_answers"]
    assert set(wrong) == {"75809", "94762"}, "the contract's wrong answers moved"
    got = daily_average(379049, 5).daily_average_paise
    assert got != 75809, "truncated instead of rounding half-up"
    assert got != 94762, "divided by the row count (4) instead of days elapsed (5)"


def test_the_fixture_actually_sums_to_the_asserted_total() -> None:
    """The fixture and the total are stated separately in the contract. If they
    ever disagree, every downstream assertion is measuring the wrong thing."""
    assert sum(e["amount_paise"] for e in FIXTURE) == EXPECTED["total_paise"] == 379049


# ── the whole payload, computed by the app ─────────────────────────────────
def _compute() -> dict:
    """Run the fixture through the application's own functions."""
    d_from = date.fromisoformat(EXPECTED["from"])
    d_to = date.fromisoformat(EXPECTED["to"])

    by_cat: dict[int | None, list[int]] = {}
    by_day: dict[date, list[int]] = {}
    for e in FIXTURE:
        c = by_cat.setdefault(e["category_id"], [0, 0])
        c[0] += e["amount_paise"]
        c[1] += 1
        d = by_day.setdefault(date.fromisoformat(e["spent_on"]), [0, 0])
        d[0] += e["amount_paise"]
        d[1] += 1

    return build_summary(
        from_=d_from, to=d_to,
        elapsed=EXPECTED["days_elapsed"],
        headline_total_paise=sum(e["amount_paise"] for e in FIXTURE),
        headline_count=len(FIXTURE),
        category_totals=[CategoryTotal(k, v[0], v[1]) for k, v in by_cat.items()],
        day_totals=[DayTotal(k, v[0], v[1]) for k, v in by_day.items()],
        names=CATEGORIES,
    )


@pytest.mark.parametrize(
    "field",
    ["from", "to", "total_paise", "total", "count", "days_elapsed",
     "daily_average_paise", "daily_average"],
)
def test_headline_field_matches_the_expected_payload(field: str) -> None:
    """Parametrised so a mismatch names the field rather than dumping a diff."""
    assert _compute()[field] == EXPECTED[field]


def test_by_category_matches_the_expected_payload_exactly() -> None:
    """Order, labels, colours, totals, counts and percentages."""
    assert _compute()["by_category"] == EXPECTED["by_category"]


def test_by_day_matches_the_expected_payload_exactly() -> None:
    """All 31 rows, including the 27 days with no spending."""
    got = _compute()["by_day"]
    assert len(got) == len(EXPECTED["by_day"]) == 31
    assert got == EXPECTED["by_day"]


# ── the properties behind the payload ──────────────────────────────────────
def test_percentages_sum_to_exactly_100() -> None:
    """Bible `E3-S3`. Floors alone give 97 here; largest-remainder makes 100."""
    assert sum(b["percent"] for b in _compute()["by_category"]) == 100


def test_breakdown_sums_to_the_headline_when_unfiltered() -> None:
    """`P-UND-05`'s invariant — asserted only with no category filter, which is
    the precondition `CV-15` had to add because nothing stated it."""
    s = _compute()
    assert sum(b["total_paise"] for b in s["by_category"]) == s["total_paise"]


def test_uncategorised_is_last_even_though_it_is_the_smallest() -> None:
    s = _compute()
    assert s["by_category"][-1]["category_id"] is None
    assert s["by_category"][-1]["category_name"] == "Uncategorised"
    assert s["by_category"][-1]["color"] == "#928a85"


def test_uncategorised_stays_last_when_it_is_the_LARGEST() -> None:
    """"Always last **regardless of size**" is the part a naive sort gets wrong,
    and the seeded fixture cannot catch it — its null bucket is the smallest."""
    rows = build_by_category(
        [CategoryTotal(1, 100, 1), CategoryTotal(None, 999_999, 1)],
        {1: ("Groceries", "#4a7c59")},
    )
    assert rows[-1]["category_id"] is None
    assert rows[-1]["total_paise"] == 999_999


def test_every_response_integer_is_an_int_never_a_decimal() -> None:
    """`SUM()` over a bigint returns `numeric` and arrives as a `Decimal`
    (`SIT-E2-S5-05`). A `Decimal` reaching the response model is the failure."""
    s = _compute()
    for key in ("total_paise", "count", "days_elapsed", "daily_average_paise"):
        assert type(s[key]) is int, f"{key} is {type(s[key]).__name__}, not int"
    for b in s["by_category"]:
        for key in ("total_paise", "count", "percent"):
            assert type(b[key]) is int


# ── rounding ───────────────────────────────────────────────────────────────
def test_three_paise_over_two_days_is_two_not_one() -> None:
    """`SIT-E2-S6-04`. 1.5 rounds UP. Python's `round()` is banker's rounding
    and would return 2 here and 2 for 2.5 — this is why it is not used."""
    assert half_up(3, 2) == 2


@pytest.mark.parametrize("total,div,want", [(0, 5, 0), (1, 2, 1), (5, 2, 3), (379049, 5, 75810)])
def test_half_up_cases(total: int, div: int, want: int) -> None:
    assert half_up(total, div) == want


def test_no_elapsed_days_is_none_never_zero() -> None:
    """`SW-ADR-053`: a wholly future range has no average. `0` would read as
    "spent nothing", on the first screen every new user sees."""
    avg = daily_average(0, 0)
    assert avg.daily_average_paise is None
    assert avg.daily_average is None


# ── the money boundary ─────────────────────────────────────────────────────
@pytest.mark.parametrize("raw,paise", [("1250.00", 125000), ("0.01", 1), ("99.99", 9999),
                                       ("1250.0", 125000), ("1250", 125000)])
def test_accepted_amounts(raw: str, paise: int) -> None:
    assert parse_amount(raw) == paise


@pytest.mark.parametrize("raw,rule", [
    ("1.25e3", "amount.grammar"),       # scientific notation
    (" 12.50 ", "amount.grammar"),      # surrounding whitespace
    ("+12.50", "amount.grammar"),       # leading plus
    (".50", "amount.grammar"),          # bare fraction
    ("abc", "amount.grammar"),
    ("1,250.00", "amount.grammar"),     # thousands separator
    (1250.00, "amount.grammar"),        # a JSON NUMBER — CV-21, never field.type
    (0.1 + 0.2, "amount.grammar"),      # the float that is 0.30000000000000004
    ("1250.0000", "amount.scale"),      # written scale, though the extras are zeros
    ("12.345", "amount.scale"),
    ("0", "amount.bounds"),
    ("0.00", "amount.bounds"),
    ("-1.00", "amount.bounds"),
    ("10000000000.01", "amount.bounds"),
])
def test_rejected_amounts_name_the_right_rule(raw: object, rule: str) -> None:
    """The rule id matters as much as the rejection: it selects the message and
    the `field` the client is shown, and `12.345` must return the scale
    sentence `P-REC-01` quotes — not the grammar one."""
    with pytest.raises(AmountError) as exc:
        parse_amount(raw)
    assert exc.value.rule == rule


def test_a_float_amount_never_round_trips() -> None:
    """Art V.1, stated as a test: the classic float artefact is refused rather
    than stored as 0.30000000000000004 or silently rounded to 0.30."""
    with pytest.raises(AmountError):
        parse_amount(0.1 + 0.2)


@pytest.mark.parametrize("paise,shown", [(379049, "3790.49"), (75810, "758.10"),
                                         (9999, "99.99"), (1, "0.01"), (0, "0.00"),
                                         (100, "1.00")])
def test_display_strings(paise: int, shown: str) -> None:
    """Trailing zeros kept — `758.10`, never `758.1`. No grouping: `en-US` is
    the client's job at render time (`P-UND-07`)."""
    assert to_display(paise) == shown


# ── largest remainder ──────────────────────────────────────────────────────
def test_largest_remainder_ties_go_to_the_earlier_position() -> None:
    """`CV-17`. Three equal parts cannot split 100 evenly; the extra point goes
    to the first, by rule rather than by sort stability."""
    assert largest_remainder([1, 1, 1], 3) == [34, 33, 33]


def test_largest_remainder_always_sums_to_100() -> None:
    for parts in ([1, 1, 1], [1, 2, 3, 4], [999, 1], [5, 5, 5, 5, 5, 5, 5]):
        assert sum(largest_remainder(parts, sum(parts))) == 100


def test_largest_remainder_of_nothing_is_zeroes_not_a_crash() -> None:
    """An empty range: `by_category` is `[]`, but a filter matching nothing can
    still produce buckets summing to zero. Dividing by that must not raise."""
    assert largest_remainder([0, 0], 0) == [0, 0]


# ── the day series ─────────────────────────────────────────────────────────
def test_empty_range_still_returns_a_full_series_of_zero_days() -> None:
    """`P-UND-06`: zeros and `[]`, never `null` — and the day series is still
    full length, because the days elapsed whether or not money was spent."""
    rows = build_by_day(date(2026, 8, 1), date(2026, 8, 31), [])
    assert len(rows) == 31
    assert all(r["total_paise"] == 0 and r["count"] == 0 for r in rows)


def test_a_single_day_range_has_one_row() -> None:
    assert len(build_by_day(date(2026, 8, 5), date(2026, 8, 5), [])) == 1
