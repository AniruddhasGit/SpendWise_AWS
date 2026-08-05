# SW-ADR-096 — The application calendar is Asia/Kolkata

| Field | Value |
|---|---|
| ADR | `SW-ADR-096` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-TZ-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-TZ-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-TZ-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

`APP_TIMEZONE=Asia/Kolkata`, named once in settings. The server computes 'today' and all chip boundaries in it. `spent_on` is never defaulted server-side — the browser always sends it explicitly. `R-UND-04` and the 75,810 gate value lose their PROVISIONAL marker.

## Why

The product is fixed at INR by the client's own ruling and the client is its population. Every alternative is worse: a UTC 'today' makes the headline average jump 20-25% every IST morning; a client-supplied 'today' makes the never-waivable gate value depend on the caller; a per-user timezone column is enterprise machinery on a learning project.

## Reversibility

**NO** on the write path — the submission instant is never stored, so rows misfiled across a day boundary can never be identified later. The practical veto window stays open until the first real (non-fixture) expense row is written.

> **⚠ FIRST IN THE CLIENT DIGEST.** This ruling formally crosses a line the register
> reserved. It is made under the client's escalation grant and is theirs to reverse.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-TZ-01`, which is marked RULED in Article X with a pointer here.*
