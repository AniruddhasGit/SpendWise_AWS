# SW-ADR-125 — Rotating the JWT secret revokes every session automatically

| Field | Value |
|---|---|
| ADR | `SW-ADR-125` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-ROTATE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-ROTATE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-ROTATE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

A one-row `app_meta` table stores the SHA-256 **fingerprint** of the current `JWT_SECRET`. At boot, if the fingerprint differs, the app revokes every live session, stores the new fingerprint, and logs one INFO line ('JWT secret rotated — N sessions revoked'). No overlap window, no dual-secret support in v1. Documented in `.env.example` and the runbook.

## Why

Without this, rotation silently signs everyone out while the admin dashboard reports active sessions that no longer exist — the app lying about its own state. Twenty lines of boot code make the truth automatic instead of depending on an operator remembering a manual step.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-ROTATE-01`, which is marked RULED in Article X with a pointer here.*
