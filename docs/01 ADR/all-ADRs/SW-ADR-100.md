# SW-ADR-100 — Deactivation enforces at all three points

| Field | Value |
|---|---|
| ADR | `SW-ADR-100` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-DEACT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-DEACT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-DEACT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

(1) Login refused with the same generic 401 as any bad credential, bcrypt compare still run. (2) All live sessions revoked in the same transaction as the toggle, audit-logged. (3) `get_current_user` re-checks `is_active` and fails closed with code `ACCOUNT_DEACTIVATED` and the message 'Your account has been deactivated. Contact your administrator.' Reactivation never resurrects old sessions.

## Why

Deactivation is the admin's only containment tool, so a flag guarding only a login form is not containment. Generic at login preserves the `§10.5` posture of revealing nothing pre-authentication; explicit mid-session is honest where there is nothing left to hide.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-DEACT-01`, which is marked RULED in Article X with a pointer here.*
