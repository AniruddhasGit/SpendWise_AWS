"""The summary computation — pure, and therefore provable without a database.

The repository returns **ids and totals only**; this module turns those into the
response the dashboard renders. Category *names* arrive from the categories
service, never from a SQL join — the one sanctioned crossing (`SW-ADR-017`),
which is service-to-service.

Keeping this pure is what lets the day-one gate's arithmetic be verified before
an RDS instance exists. The database's job is to return the right rows; this
module's job is to turn right rows into the right number, and the two failures
are worth separating.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from app.core.money import daily_average, largest_remainder, to_display

# The synthetic bucket. It is a BUCKET, not a row in `categories` — nothing
# joins to it, and `SW-ADR-131` puts it last regardless of size.
UNCATEGORISED_NAME = "Uncategorised"
UNCATEGORISED_COLOR = "#928a85"
# Changed 2026-08-21 by `CR-002`/`SW-ADR-152` — and this line is the reason
# that change request has a defect section. The band is a SERVER value: the
# ribbon and donut paint `b.color` straight from this response, so the CSS
# token `--sw-cat-uncat` is NOT what renders it. Moving the token alone left
# `tools/contrast.py` reporting PASS on a colour the app did not use, while
# the browser drew the failing one. `consistency_check.py` now asserts this
# constant, the design-system token and the API contract are the same hex.


@dataclass(frozen=True, slots=True)
class CategoryTotal:
    """What the repository returns per category: an id and integers."""

    category_id: int | None
    total_paise: int
    count: int


@dataclass(frozen=True, slots=True)
class DayTotal:
    """One calendar day. Present even when nothing was spent (`SRC-001 §7.4`)."""

    date: date
    total_paise: int
    count: int


def build_by_category(
    totals: list[CategoryTotal],
    names: dict[int, tuple[str, str]],
) -> list[dict]:
    """Order the buckets, label them, and compute percentages that sum to 100.

    `names` maps `category_id -> (name, colour)` and comes from the categories
    **service**. A missing id would be a broken foreign key rather than a
    display problem, so it is not papered over with a placeholder.

    Order: `total_paise` descending, then name ascending, with the synthetic
    `null` bucket **always last regardless of size** (`SW-ADR-131`). Sorting
    happens *before* the percentage pass, because the tie-break is positional.
    """
    real = sorted(
        (t for t in totals if t.category_id is not None),
        key=lambda t: (-t.total_paise, names[t.category_id][0]),
    )
    synthetic = [t for t in totals if t.category_id is None]
    ordered = real + synthetic

    # The denominator is the SUM OF THE BUCKETS, not the headline total. They
    # are equal with no filter; under a category filter the headline re-scopes
    # and this does not (CV-03/CV-15), and dividing by the headline would print
    # percentages summing to several hundred.
    bucket_sum = sum(t.total_paise for t in ordered)
    percents = largest_remainder([t.total_paise for t in ordered], bucket_sum)

    out = []
    for t, pct in zip(ordered, percents):
        name, colour = (
            names[t.category_id] if t.category_id is not None
            else (UNCATEGORISED_NAME, UNCATEGORISED_COLOR)
        )
        out.append({
            "category_id": t.category_id,
            "category_name": name,
            "color": colour,
            "total_paise": t.total_paise,
            "count": t.count,
            "percent": pct,
        })
    return out


def build_by_day(from_: date, to: date, rows: list[DayTotal]) -> list[dict]:
    """One row per calendar day, **including days with no spending**.

    In SQL this is `generate_series` LEFT JOINed to `expenses`, with the owner
    predicate in `ON` and never `WHERE` — in `WHERE` the LEFT JOIN degenerates
    to an INNER JOIN and the zero days silently vanish. This function fills the
    gaps the same way, so the two implementations agree and a test can compare
    them.
    """
    seen = {r.date: r for r in rows}
    out, day = [], from_
    while day <= to:
        r = seen.get(day)
        out.append({
            "date": day.isoformat(),
            "total_paise": r.total_paise if r else 0,
            "count": r.count if r else 0,
        })
        day += timedelta(days=1)
    return out


def build_summary(
    *,
    from_: date,
    to: date,
    elapsed: int,
    headline_total_paise: int,
    headline_count: int,
    category_totals: list[CategoryTotal],
    day_totals: list[DayTotal],
    names: dict[int, tuple[str, str]],
) -> dict:
    """Assemble the whole response. Keyword-only, because six integers in a row
    is an argument order somebody will get wrong exactly once.

    `elapsed` is passed in rather than computed here so that the clock stays a
    dependency and this stays pure.
    """
    avg = daily_average(headline_total_paise, elapsed)
    return {
        "from": from_.isoformat(),
        "to": to.isoformat(),
        "total_paise": headline_total_paise,
        "total": to_display(headline_total_paise),
        "count": headline_count,
        "days_elapsed": elapsed,
        # None, never 0, when nothing has elapsed — 0 reads as "spent nothing"
        "daily_average_paise": avg.daily_average_paise,
        "daily_average": avg.daily_average,
        "by_category": build_by_category(category_totals, names),
        "by_day": build_by_day(from_, to, day_totals),
    }
