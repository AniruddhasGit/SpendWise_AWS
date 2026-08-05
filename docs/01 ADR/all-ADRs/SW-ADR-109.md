# SW-ADR-109 — Selecting a category re-scopes everything below the ribbon

| Field | Value |
|---|---|
| ADR | `SW-ADR-109` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-RIBBON-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-RIBBON-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-RIBBON-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Total, entry count, daily average, per-day bars **and** the entry list all re-scope, served by the existing single summary call taking an optional `category_id`. **The ribbon itself stays computed over the whole period across all categories** — selected band emphasized, others dimmed — so proportions stay visible and other bands stay reachable. Clicking the active band again clears the filter.

## Why

If the headline does not follow, the page shows a total that visibly disagrees with the per-day subtotals printed directly beneath it, in an app whose entire job is adding numbers up. Keeping the ribbon period-scoped preserves 'the chart and the filter are the same object': the object shows the whole and scopes the rest.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-RIBBON-01`, which is marked RULED in Article X with a pointer here.*
