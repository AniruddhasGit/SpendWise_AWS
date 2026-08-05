# SW-ADR-085 — Correcting `SW-ADR-052`'s worked example

| Field | Value |
|---|---|
| ADR | `SW-ADR-085` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-052` |
| Raised by | QA FINDING-22 (LOW) — arithmetic in the prose |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-052` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-052`'s decision is right and stands. Its worked example is muddled: it says the Aug-5 entry drops out under half-open semantics. It does not — half-open drops Aug **31**, on which nothing was spent — and the figure quoted (94,762) proves the entry did not drop, since it equals 379,049 ÷ 4.

## Decision

**Restated: half-open applied to the **elapsed count** gives 4 days rather than 5 while the numerator is unchanged, yielding 94,762 against the agreed 75,810. The 25% error and the conclusion are unaffected.**

## Consequences

- This is the ADR that makes the never-waivable gate deterministic, so its arithmetic is read closely by exactly the people who must not be confused by it.

---

*A superseding record, not an edit. `SW-ADR-052` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
