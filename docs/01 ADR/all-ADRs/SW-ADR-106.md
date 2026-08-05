# SW-ADR-106 — The admin session list shows no IP and no user agent

| Field | Value |
|---|---|
| ADR | `SW-ADR-106` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-SESSFIELDS-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-SESSFIELDS-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-SESSFIELDS-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Shows user (email, display name), `issued_at`, `last_seen_at`, and status. Nothing else. `ip` and `user_agent` remain **stored** for forensics but appear in no admin response model — the Pydantic model physically lacks the fields.

## Why

`§9.3` asks only for 'last active and status', and a screen mapping every user to approximate location and device is more personally revealing than much of what `§4.5` protects. A literal reading of a prohibition is not a grant.

## Reversibility

yes — surfacing later is a deliberate model change plus an ADR

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-SESSFIELDS-01`, which is marked RULED in Article X with a pointer here.*
