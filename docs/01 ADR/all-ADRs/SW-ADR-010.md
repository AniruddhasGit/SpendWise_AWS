# SW-ADR-010 — The day-one business rule: daily average = total divided by days elapsed

| Field | Value |
|---|---|
| ADR | `SW-ADR-010` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT_RULE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S7.4` · `SRC-002 §11` |

## Context

SRC-001 S7.4 requires the summary endpoint to return a daily average but does not define the denominator. Three readings are defensible and they differ by an order of magnitude. The day-one proof needs the client's written expected answer for known inputs, or there is nothing to prove.

## Options considered

- A. Total / days ELAPSED in the range, capped at today - RECOMMENDED.
- B. Total / days WITH SPENDING.
- C. Total / days IN RANGE.

## Decision

**A. Total divided by days elapsed, capped at today. Computed in integer minor units, rounded half-up to the nearest minor unit.**

## Consequences

- WORKED EXAMPLE, AGREED - this is the acceptance value the day-one gate checks against:
-   Range 1-31 Aug, today the 5th. Expenses Rs1,250.00 (Aug 1), Rs340.50 (Aug 3), Rs2,100.00 (Aug 3), Rs99.99 (Aug 5).
-   Total 379,049 paise . count 4 . days elapsed 5 . EXPECTED DAILY AVERAGE = 75,810 paise (Rs758.10)
- The application computes this from seeded rows. A fixture asserting on itself does not satisfy the gate.
- Rejected: days-with-spending (Rs1,263.50) and days-in-range (Rs122.27).

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
