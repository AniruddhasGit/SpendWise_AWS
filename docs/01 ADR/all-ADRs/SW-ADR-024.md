# SW-ADR-024 — All timestamps are TIMESTAMPTZ, NOT NULL, stored in UTC

> **⚠ AMENDED 2026-08-05 by `SW-ADR-076` (QA FINDING-10 (HIGH)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-024` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.2` · `SRC-001 §6.6` · `SW-ADR-025` |

## Context

SRC-001 defines eleven timestamp columns across §6.2-§6.7 and never says whether they carry a timezone, what precision they hold, or what they default to.

## Options considered

- A. TIMESTAMPTZ NOT NULL, microsecond precision, DEFAULT now(), stored UTC.
- B. Naive TIMESTAMP.
- C. Epoch integers.

## Decision

**A. TIMESTAMPTZ everywhere, NOT NULL, DEFAULT now(), values stored in UTC.**

## Consequences

- `spent_on` remains a DATE — it is a calendar day the user chose, not an instant, and SW-ADR-025 defines which calendar it belongs to.
- Naive timestamps were rejected outright: this application computes a per-day breakdown, and a naive column makes the day boundary undiscoverable after the fact.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
