# SW-ADR-054 — The empty-range summary payload

| Field | Value |
|---|---|
| ADR | `SW-ADR-054` |
| Pack | `SPENDWISE_V1` |
| Type | API_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §7.4` · `SW-ADR-053` |

## Context

Nothing says what the summary returns when a range contains no expenses. This is the FIRST screen every new user sees: eight seeded categories, zero expenses.

## Options considered

- A. Zeros everywhere: total 0, count 0, average null, breakdown [], the full generate_series of zero-valued days.
- B. Nulls for total and average.
- C. 204/404.

## Decision

**A, with average null per SW-ADR-053 when elapsed is zero, and a distinct first-run UI state.**

## Consequences

- C is wrong: an empty result is a successful answer, and returning no body breaks the one-round-trip contract of SRC-001 §7.4.
- The frontend must never render zeros for ABSENT data — in a money app, '0.00' from a failed request is indistinguishable from a true zero. That is a separate state, covered by SW-ADR-057.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
