# SW-ADR-102 — Registration reveals duplicates; login stays dark

| Field | Value |
|---|---|
| ADR | `SW-ADR-102` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-ENUM-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-ENUM-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-ENUM-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Registration returns **409, 'An account with this email already exists.'** Login keeps the full `§10.5` timing defence unchanged, and deactivation stays invisible at login. Registration is rate-limited (5/min, 20/day per IP) so bulk enumeration is bounded and logged.

## Why

The non-enumerable pattern requires an email channel ('we sent you a link') and this stack has none by the client's own ruling — a fake success would strand a real person in a product whose only recovery is one human admin. The login path, the one attackers script, stays dark.

## Reversibility

yes — a response-message change

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-ENUM-01`, which is marked RULED in Article X with a pointer here.*
