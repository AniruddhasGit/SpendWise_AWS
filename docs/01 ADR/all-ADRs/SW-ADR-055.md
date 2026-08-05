# SW-ADR-055 — Ribbon geometry, band ordering, and percentage rounding

| Field | Value |
|---|---|
| ADR | `SW-ADR-055` |
| Pack | `SPENDWISE_V1` |
| Type | UX_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §9.2` |

## Context

SRC-001 §9.2 asks for one horizontal bar split 'in true proportion' and gives no rounding or ordering rule. Three categories at exactly one third each round to 33.3% and leave 0.1% of the bar unfilled, or to 33.34% and overflow it. Band order is equally unstated, so an unordered GROUP BY can lay the same data out differently on two consecutive loads.

## Options considered

- A. Exact fractional widths for geometry, largest-remainder rounding for any printed percentage, bands ordered total DESC then name ASC.
- B. Round the widths too.
- C. Print amounts instead of percentages.

## Decision

**A.**

## Consequences

- Geometry and label are decoupled: the bar is always exactly full, and the printed numbers always sum to 100.
- Deterministic ordering means the same data always renders the same way, which is also what makes the ribbon testable.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
