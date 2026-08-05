# SW-ADR-146 — The gate has a date, and it is now written down

| Field | Value |
|---|---|
| ADR | `SW-ADR-146` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | — |
| Raised by | GOAL_14 — the wall clock rolled over to 2026-08-06 mid-build |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-06 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-010` · `SW-ADR-039` · `SW-ADR-085` · `CV-14` · `CV-20` · Art IX.4 |

## Context

At midnight, four assertions in `test_gate_75810.py` went red with no code change behind them.

The never-waivable value is `daily_average_paise = 75810`, and `days_elapsed` is
`min(to, today) - from + 1` (`SW-ADR-085`, inclusive both ends). Over the 1–31 August range the
divisor is therefore **however many days of August have happened**:

| evaluated on | days elapsed | 379049 ÷ days, half-up |
|---|---|---|
| 2026-08-05 | 5 | **75810** ✓ |
| 2026-08-06 | 6 | 63175 |
| 2026-08-07 | 7 | 54150 |
| 2026-09-01 | 31 | 12227 |

`contract.json`'s `gate` block stated the request, the range, the field, the value, the rounding
formula and **three wrong answers a plausible implementation would produce** — and never the date
the whole thing is evaluated on. `expected_summary.json` carries `days_elapsed: 5`, which implies
it; nothing states it.

So the in-process gate tests read the system clock. They were written on 2026-08-05 and passed on
2026-08-05. On every other day in history they would have failed.

**The browser tests always had it right.** `APP_TODAY_OVERRIDE=2026-08-05` was set in
`tests/browser/conftest.py` from the first line of it, because a browser test cannot reach an
in-process dependency override and `CV-14` had already worked that out. The in-process ones
inherited the machine's date and nobody noticed, because the day they were written was the day
they were pinned to.

That is the failure mode this document set has caught in itself five times now, in its purest
form: **a value was pinned and the thing it was pinned to was not**, and the only evidence was a
test that passed.

## Decision

**A. `gate.as_of` joins the contract**, with `as_of_note` stating the arithmetic and the three
values the neighbouring days produce. The date is now a fact of record rather than an inference
from `days_elapsed: 5` in a generated file.

**B. `test_gate_75810.py` reads `GATE["as_of"]` and pins `APP_TODAY_OVERRIDE` to it** — via an
**autouse** fixture, because it must run before the `client` fixture, which clears the settings
cache and re-imports the application. The date is never typed into the test.

**C. `--check` on `client/sync_tokens.py` joins `consistency_check.py`**, with a plant that drifts
one hex digit. Unrelated to the clock, added in the same pass for the same reason: the client's
copy of the design tokens is the other artifact whose correctness lives in a different file from
its value.

## Consequences

- The gate is now reproducible on any day, on any machine, in any CI run. It was not before, and
  a green run on 2026-08-05 was the only evidence that existed either way.
- **The clock is a dependency.** `CV-06` already refused a library that freezes the process clock,
  because it would not freeze `now()` inside PostgreSQL. The remaining half of that thought — that
  any test asserting a value derived from *today* must state which today — was never written.
  It is written here.
- Sixteen checks in `consistency_check.py`, all red-proofed. None of them can catch this class:
  a test that reads the environment is not a cross-reference that fails to resolve. What caught it
  was **time passing**, which is the cheapest reviewer in the project and the only one that
  cannot be argued with.

---

*Ruled under `SW-ADR-015`.*
