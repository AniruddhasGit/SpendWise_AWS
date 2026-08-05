# SW-ADR-053 — The daily-average formula, written literally

| Field | Value |
|---|---|
| ADR | `SW-ADR-053` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT_RULE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-010` · `SW-ADR-052` |

## Context

SW-ADR-010 ruled 'days elapsed, capped at today' in words and gave one worked example. It is undefined for any range that does not contain today: for a closed historical month one reading makes the average shrink a little every day, and for a wholly future range both readings go to zero or negative — dividing by zero, or printing a negative average against positive spending.

## Options considered

- A. elapsed = max(0, min(to, today) - from + 1); average is null when elapsed is 0.
- B. today - from + 1.
- C. Reject ranges starting after today.

## Decision

**A. Written as a formula, not a sentence.**

## Consequences

- Keeps a closed historical period stable — July read today and July read next month give the same number.
- A null average is a specified value the frontend renders as a dash, not an error.
- Does not change the agreed 75,810 for the worked example.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
