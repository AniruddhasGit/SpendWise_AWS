# SW-ADR-138 — The API contract is generated from a spec of record, not written by hand

| Field | Value |
|---|---|
| ADR | `SW-ADR-138` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice run 2 — contradictions C1…C7 and C11, all inside one hand-written section |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-051` · `SW-ADR-066` · `SRC-001 §7.4` · `SW-ADR-053` · `SW-ADR-055` · `SW-ADR-092` · `SW-ADR-131` |

## Context

The first uncoached slice asked eighteen questions, **eight of them variants of one**: *what does
the JSON actually look like?* The PRD specified behaviour in prose for ~2,500 lines and contained
a single JSON block. The fix was to hand-write two worked payloads into §6.1 and label them
**normative**.

The second slice read that section and found, inside it:

| | The hand-written §6.1 said | Everything else said |
|---|---|---|
| C1 | no `by_day` at all | `SRC-001 §7.4` requires one row per calendar day; five documents assert on it, and `SIT-E0-S9-05` asserts on a field whose **name did not exist** |
| C2 | `daily_average_paise` is `0` when nothing elapsed | `null` — `SW-ADR-053`, `SW-ADR-054`, `P-UND-02`, `R-UND-04`, `06_summary_sequence.md`, `SIT-E2-S6-03` |
| C3 | the gate range is 1–5 Aug | 1–31 Aug — `SW-ADR-010` and `SIT-E0-S9-01` |
| C4 | categories "Food" and "Bills" | `SW-ADR-092` rules eight names; **neither is one of them** |
| C5 | "ordered by `total_paise` descending" | over an array printed `125000, 210000, 34050, 9999` |
| C6 | no `color`, no `percent` | `P-UND-05` requires both; Bible `E3-S3` requires percentages summing to 100 |
| C11 | half-up rounding `[SRC: SW-ADR-085]` | `SW-ADR-085` is about inclusive date ranges. Half-up is `SW-ADR-010` — the wrong provenance on the one number that is never waivable |

Seven contradictions, in one section, written to end contradictions. **A hand-written example is
exactly as driftable as the prose it replaces — and once labelled normative, it drifts with
authority.**

## Decision

**`docs/03 PRD/api/contract.json` is the spec of record for the API contract.** Three artifacts
are generated from it by `generate_api.py`, and `consistency_check.py` runs `--check`:

1. **`docs/06 DataModel/seed/expected_summary.json`** — the complete gate payload, **computed**
   from the seed fixture: totals summed, the average taken half-up in integers, buckets ordered,
   percentages by largest remainder, all 31 day rows emitted including the empty ones.
2. **`docs/03 PRD/api/error_codes.md`** — the registry `SW-ADR-051` said in its own Consequences
   was *"the only thing that lets the PRD write a binary acceptance criterion for an error path"*,
   and then never produced. Eleven codes, closed list.
3. **PRD §6.1**, injected between markers.

**The generator asserts the gate before writing anything.** If `contract.json` ever computes an
average other than `75810` from its own fixture, it exits non-zero and emits nothing — the spec
cannot disagree with itself and still produce an artifact.

**Three things that were unstated are now stated**, because a computed payload cannot leave them
blank: the day-series field is **`by_day`** with `{date, total_paise, count}`; the seed fixture
**assigns a category to each of the four expenses**; `daily_average_paise` is **`null`, never
`0`**, when nothing has elapsed.

## Consequences

- **The ordering rule and the example can no longer disagree**, because the example is produced
  by the rule. C5 is not fixed, it is made unrepresentable.
- The category names in the payload come from `SW-ADR-092`'s ruled list by construction, so C4
  cannot recur.
- This is the pattern `06 DataModel` already proved: a spec of record, generated artifacts, and a
  `--check` that regenerates and compares. **The API layer — the layer the code is written from —
  was the last major artifact still maintained by hand**, and it was the only one where a cold
  reader found a contradiction in every section they needed.
- What is still hand-written: the prose in §4 that explains *why*. That part cannot be generated,
  and it is not the part that drifted.
