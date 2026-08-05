# SW-ADR-118 — The custom range is bounded

| Field | Value |
|---|---|
| ADR | `SW-ADR-118` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-RANGECAP-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-RANGECAP-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-RANGECAP-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

`from > to` -> 422. Maximum custom span **400 days** — longer spans 422 naming the cap. Lower bound `from >= 2000-01-01`. 'This year' (max 366 day rows) fits comfortably. Coarser bucketing for longer spans is fast-follow.

## Why

An unbounded range returns thousands of day rows and sub-pixel bars for no product value. 400 days covers every chip including a full year with margin.

## Reversibility

yes — one constant

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-RANGECAP-01`, which is marked RULED in Article X with a pointer here.*
