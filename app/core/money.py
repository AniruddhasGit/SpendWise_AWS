"""Integer paise. Never a float, at any point (`CONSTITUTION` Art V.1).

`Decimal` at the boundary, `int` everywhere inside, a display string at render
time only. `SUM()` over a bigint returns `numeric` and arrives as a `Decimal` —
cast it back or one reaches the response model (Art V.2).

Every function here is **pure** — no database, no clock, no I/O — which is why
the day-one gate's arithmetic can be proved correct before an RDS instance
exists.

The wrong answers this module exists to prevent, each of which looks plausible:

* **75809** — truncating instead of rounding half-up. Fails the gate by one paisa.
* **94762** — dividing by the row count (4) instead of days elapsed (5).
* **0.30000000000000004** — a float anywhere near money.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

# `serialisation.amount_grammar` in docs/03 PRD/api/contract.json.
# Checks SHAPE, not scale: the scale rule counts decimal places and owns
# P-REC-01's sentence. An earlier version capped the fraction at two digits AND
# ran before the scale rule, which made the scale rule unreachable dead text.
AMOUNT_GRAMMAR = re.compile(r"^-?[0-9]{1,15}(\.[0-9]+)?$")

MAX_PAISE = 10 ** 12          # SW-ADR-079 — the cast overflows, not the sum
PAISE_PER_RUPEE = 100


class AmountError(ValueError):
    """Carries the contract's rule id, so the caller looks up the message and
    the `field` from the registry rather than inventing a sentence here."""

    def __init__(self, rule: str) -> None:
        super().__init__(rule)
        self.rule = rule


def parse_amount(raw: object) -> int:
    """A client-supplied amount -> integer paise, or `AmountError`.

    Rules apply in the order `error_codes.precedence` states, stopping at the
    first failure: `amount.grammar` -> `amount.scale` -> `amount.bounds`.

    `raw` is typed `object` deliberately. `amount` is modelled `Any` and
    grammar-checked so a JSON *number* returns `amount.grammar` rather than
    `field.type` (`CV-21`) — a float has already lost the value by the time it
    reaches us, so there is nothing to salvage and nothing to round.
    """
    if not isinstance(raw, str) or not AMOUNT_GRAMMAR.fullmatch(raw):
        raise AmountError("amount.grammar")

    try:
        d = Decimal(raw)
    except InvalidOperation:                    # pragma: no cover — grammar precludes it
        raise AmountError("amount.grammar") from None

    # WRITTEN scale, not numeric value (CV-04). "1250.0000" is refused even
    # though the extra places are zeros: the rule is on what the person typed.
    if -d.as_tuple().exponent > 2:
        raise AmountError("amount.scale")

    paise = int(d.scaleb(2))                    # exact — scale <= 2 guaranteed above
    if not (0 < paise <= MAX_PAISE):
        raise AmountError("amount.bounds")
    return paise


def to_display(paise: int) -> str:
    """Integer paise -> a two-place decimal string. `379049` -> `"3790.49"`.

    No thousands separators. `en-IN` grouping (₹12,34,567.89) is the client's
    job, at render time only (`P-UND-07`) — a server that groups has committed
    to a locale it cannot know.
    """
    sign = "-" if paise < 0 else ""
    p = abs(paise)
    return f"{sign}{p // PAISE_PER_RUPEE}.{p % PAISE_PER_RUPEE:02d}"


def half_up(total: int, divisor: int) -> int | None:
    """Round-half-up division, in integers only.

    `(2·total + divisor) // (2·divisor)`. No `Decimal`, no `round()` — Python's
    `round()` is banker's rounding, which gives 2 for both 1.5 and 2.5 and is
    not what `SW-ADR-010` ruled.

    Returns **`None`** when the divisor is zero, never `0`: a wholly future
    range has no average, and `0` reads as "spent nothing" (`SW-ADR-053`).
    """
    if divisor == 0:
        return None
    return (2 * total + divisor) // (2 * divisor)


def largest_remainder(parts: list[int], total: int) -> list[int]:
    """Percentages that sum to **exactly** 100 (`SW-ADR-055`).

    Integer arithmetic throughout. Ties go to the **earlier position** in the
    already-sorted list (`CV-17`) — stated rather than left to sort stability,
    because an accident is not a rule.

    `total` is the **sum of the buckets**, not the headline total. They are
    identical with no filter; under a category filter the headline re-scopes and
    the breakdown does not (`CV-03`, `CV-15`), so dividing by the headline would
    print percentages summing to several hundred.
    """
    if total <= 0:
        return [0] * len(parts)
    floors = [p * 100 // total for p in parts]
    remainders = [p * 100 - f * total for p, f in zip(parts, floors)]
    short = 100 - sum(floors)
    for i in sorted(range(len(parts)), key=lambda i: (-remainders[i], i))[:short]:
        floors[i] += 1
    return floors


@dataclass(frozen=True, slots=True)
class Average:
    """The daily average, with the inputs that produced it.

    Carries `days_elapsed` because it is the most-guessed value in this project:
    the divisor is **days, not rows**. Returning it beside the answer makes a
    wrong denominator visible in the response instead of hidden in it.
    """

    total_paise: int
    days_elapsed: int
    daily_average_paise: int | None

    @property
    def daily_average(self) -> str | None:
        if self.daily_average_paise is None:
            return None
        return to_display(self.daily_average_paise)


def daily_average(total_paise: int, days_elapsed: int) -> Average:
    """The day-one gate's arithmetic, in one place.

    `379049` over `5` elapsed days is **75810**.
    """
    return Average(total_paise, days_elapsed, half_up(total_paise, days_elapsed))
