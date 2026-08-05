# SW-ADR-036 — Expense amounts are bounded above

> **⚠ AMENDED 2026-08-05 by `SW-ADR-079` (QA FINDING-13 (MEDIUM) — premise).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-036` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.6` · `SRC-001 §7.4` · `SRC-001 §10.6` |

## Context

SRC-001 §6.6 bounds the amount below (> 0) and not above. bigint tops out near 9.2e18 paise; a few rows near that make SUM() raise 'bigint out of range', and because SRC-001 §7.4 puts the total, the breakdown and the day series in ONE endpoint, a single poisoned row 500s the entire dashboard — including the screen needed to find and delete it.

## Options considered

- A. CHECK (amount_paise > 0 AND amount_paise <= 10^12) plus the same bound in Pydantic.
- B. Catch the overflow and return an error.
- C. No bound.

## Decision

**A. Upper bound 10^12 paise (Rs 1,000 crore).**

## Consequences

- The number is arbitrary; any stated number is better than bigint's, and this one is unreachable by a real expense while still catching a mistyped digit run.
- B was rejected: the dashboard still fails, just more politely, and the offending row remains unfindable.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
