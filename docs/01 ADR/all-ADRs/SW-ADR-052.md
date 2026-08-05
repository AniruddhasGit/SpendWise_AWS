# SW-ADR-052 — Date ranges are inclusive at both ends

> **⚠ AMENDED 2026-08-05 by `SW-ADR-085` (QA FINDING-22 (LOW) — arithmetic in the prose).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-052` |
| Pack | `SPENDWISE_V1` |
| Type | API_CONTRACT |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §7.3` · `SRC-001 §7.4` · `SW-ADR-010` |

## Context

SRC-001 §7.3 and §7.4 take a date range and never state its boundary rule. Under half-open semantics the last day of every range vanishes: on SW-ADR-010's own worked example the Aug-5 entry drops out and days-elapsed becomes 4, giving 94,762 paise instead of the agreed 75,810 — a 25% error that fails the never-waivable day-one gate for entirely the wrong reason.

## Options considered

- A. Inclusive at both ends.
- B. Half-open [from, to).

## Decision

**A. `spent_on BETWEEN from AND to`, and generate_series and the days-elapsed count use the identical convention.**

## Consequences

- Half-open is the more common API default, which is exactly why this must be written down rather than assumed.
- The day-one gate is not deterministic until this is stated.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
