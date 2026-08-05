# SW-ADR-113 — Uncategorised spending is a real bucket

> **⚠ AMENDED 2026-08-05 by `SW-ADR-131`.** The colour below is `#a8a29e`, which
> measures **2.36:1** against paper — under the 3:1 floor. It is `#948c87` (3.09:1).
> Every other ruling here stands, including 'always ordered last'.

| Field | Value |
|---|---|
| ADR | `SW-ADR-113` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **SUPERSEDED_IN_PART** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-UNCAT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-UNCAT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-UNCAT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

A synthetic bucket appears in the breakdown and the ribbon whenever its total is nonzero: id null, label 'Uncategorised', colour `#a8a29e`, **always ordered last** regardless of size, clickable to filter `category_id IS NULL`. **Invariant, asserted in tests: the breakdown always sums exactly to the headline total.**

## Why

Null-category rows are guaranteed by the client's own delete rule, so dropping them makes the split sum to less than the total on the same screen. A money app may never disagree with itself.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-UNCAT-01`, which is marked RULED in Article X with a pointer here.*
