# SW-ADR-084 — Character columns are TEXT everywhere, including hashes and colours

| Field | Value |
|---|---|
| ADR | `SW-ADR-084` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-026` |
| Raised by | QA FINDING-21 (LOW) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-026` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-026` ruled TEXT + CHECK and explicitly rejected `VARCHAR(n)`. `SW-ADR-032` then specified `CHAR(64)` and `SW-ADR-034` `CHAR(7)` — a type the same pass rejected, and `CHAR(n)` is `bpchar`, which blank-pads and ignores trailing spaces in comparison. `SW-ADR-028`'s title also says VARCHAR while its decision says TEXT.

## Decision

**`token_hash` and `color` are TEXT with a CHECK — `char_length(token_hash) = 64` and the existing `^#[0-9a-f]{6}$` regex. Every character column in the schema is TEXT.**

## Consequences

- `SW-ADR-066` makes a regenerated `schema.sql` a failing test against the committed one, so a type inconsistency would have surfaced as a red build rather than a style note.
- `SW-ADR-028`'s title is wrong and its decision is right; the decision governs.

---

*A superseding record, not an edit. `SW-ADR-026` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
