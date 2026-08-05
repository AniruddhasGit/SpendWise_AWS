# SW-ADR-079 — Correcting `SW-ADR-036`: the overflow is in the cast, not the SUM

| Field | Value |
|---|---|
| ADR | `SW-ADR-079` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-036` |
| Raised by | QA FINDING-13 (MEDIUM) — premise |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-036` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-036` claimed `SUM()` over a bigint column raises 'bigint out of range'. It does not: PostgreSQL's `sum(bigint)` returns `numeric` precisely so it cannot overflow — as `SRC-001 §10.6`, cited in that ADR's own sources, says outright.

## Decision

**The upper bound stands at 10^12 paise. The reason is restated: the numeric `SUM()` cannot overflow, but Art V.2's **mandated cast back to BigInteger** can, and the CHECK constraint is what keeps that cast always safe.**

## Consequences

- Matters because anyone verifying the original claim would sum large bigints, see numeric return cleanly, conclude the ADR was alarmist, and relax a control that is genuinely needed.

---

*A superseding record, not an edit. `SW-ADR-036` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
