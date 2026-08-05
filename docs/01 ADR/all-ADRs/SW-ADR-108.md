# SW-ADR-108 — What each period chip means

| Field | Value |
|---|---|
| ADR | `SW-ADR-108` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-CHIPS-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-CHIPS-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-CHIPS-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

All boundaries in Asia/Kolkata. **This week** = Monday 00:00 of the current ISO week through Sunday. **This month** = the 1st through the last day of the current calendar month. **Last month** = the whole previous calendar month. **This year** = 1 January through 31 December. All ranges inclusive at both ends; the daily average handles the future tail via the elapsed cap.

## Why

The only set consistent with `SW-ADR-010`'s client-agreed worked example — 1–31 Aug with today the 5th — so the 75,810 gate value is reachable through the 'This month' chip on the fixture date. Full-period chips also keep a closed historical month stable when re-read later.

## Reversibility

yes — frontend range computation

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-CHIPS-01`, which is marked RULED in Article X with a pointer here.*
