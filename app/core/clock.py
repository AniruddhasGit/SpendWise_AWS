"""What "today" means, in one place.

`today_ist()` behind a dependency — never a library that freezes the process
clock, which would not freeze `now()` inside PostgreSQL (`CV-06`). Session
expiry and `spent_on` validation would then disagree about what day it is,
intermittently, near midnight.

Reads `APP_TODAY_OVERRIDE` when set, for the browser-observed gate that an
in-process dependency override cannot reach (`CV-14`, `CV-20`).

**The timezone is not a formatting detail.** `SW-ADR-096` is irreversible on the
write path: the submission instant is never stored, so a row misfiled across a
day boundary can never be identified afterwards.
"""
from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from app.core.settings import get_settings


def timezone() -> ZoneInfo:
    return ZoneInfo(get_settings().APP_TIMEZONE)


def today() -> date:
    """The current calendar date in the configured timezone.

    On a UTC server an IST user's first 5.5 hours of every day would otherwise
    count as yesterday — the headline average jumps 20-25% overnight, and on the
    1st of a month the denominator can reach zero (`OPEN-TZ-01`).
    """
    override = get_settings().APP_TODAY_OVERRIDE
    if override is not None:
        return override
    return datetime.now(timezone()).date()


def days_elapsed(from_: date, to: date, as_of: date) -> int:
    """`max(0, min(to, today) - from + 1)` — the divisor of the daily average.

    **Days, not rows.** Inclusive of both ends (`SW-ADR-085`), capped at today
    so a range running into the future does not inflate the denominator and
    deflate the average.

    Zero when the whole range is in the future — which is what makes the average
    `None` rather than `0` (`SW-ADR-053`).
    """
    return max(0, (min(to, as_of) - from_).days + 1)


def span_days(from_: date, to: date) -> int:
    """The number of `by_day` rows a range produces. Inclusive both ends, so a
    single-day range spans 1. The 400-day cap is measured against this
    (`range.span`), which is why it is a formula and not prose."""
    return (to - from_).days + 1


def spent_on_window(as_of: date) -> tuple[date, date]:
    """The accepted range for `spent_on`: today − 10 years .. today + 1 year.

    **Calendar arithmetic**, not fixed day counts (`CV-23`) — `relativedelta`
    clamps 29 February to the 28th rather than drifting by a day. Every other
    date rule in this system is calendar-based; a day-count here would disagree
    with them exactly on the boundary `NEG-M-08`/`NEG-M-09` probe.
    """
    return as_of - relativedelta(years=10), as_of + relativedelta(years=1)
