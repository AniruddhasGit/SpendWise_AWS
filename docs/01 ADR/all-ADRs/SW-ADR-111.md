# SW-ADR-111 — How far spending may be dated

| Field | Value |
|---|---|
| ADR | `SW-ADR-111` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-FUTURE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-FUTURE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-FUTURE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

`today − 10 years <= spent_on <= today + 1 year`, evaluated in Asia/Kolkata, enforced by Pydantic with 422 on create and update. The database carries a static sanity CHECK (`spent_on BETWEEN '2000-01-01' AND '2100-12-31'`). Future-dated entries within the window count in the numerator while the denominator stays capped at today — accepted, so total ÷ elapsed always reconciles with the list on screen.

## Why

Next week's rent is a real entry and refusing it is user-hostile; a mistyped year 2062 is not, and today the app accepts it silently into a range no chip can reach.

## Reversibility

yes — window constants; stored rows unaffected

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-FUTURE-01`, which is marked RULED in Article X with a pointer here.*
