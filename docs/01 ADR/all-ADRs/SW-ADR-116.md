# SW-ADR-116 — No self-service profile or password change in v1

| Field | Value |
|---|---|
| ADR | `SW-ADR-116` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-USEREDIT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-USEREDIT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-USEREDIT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Confirmed **no**, explicitly: no self-service change of email, display name or password. The only password-change route is the admin-issued reset — including an admin issuing one against themselves. Self-service password change (knowing the current password) is the first fast-follow candidate.

## Why

No source grants it; the register asked only that the 'no' be deliberate rather than an accident of the endpoint list. On a single-human deployment the admin-reset route is friction-free in practice.

## Reversibility

yes — purely additive later

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-USEREDIT-01`, which is marked RULED in Article X with a pointer here.*
