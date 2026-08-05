# SW-ADR-104 — Record failed logins; never lock

| Field | Value |
|---|---|
| ADR | `SW-ADR-104` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-LOCKOUT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-LOCKOUT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-LOCKOUT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Every failed login emits one structured WARN line — normalized email, source IP, user agent, request_id. **No account-lockout mechanism in v1**; brute force is bounded by the rate limits. `§1`'s 'locks themselves out' is read as the colloquial state — forgot the password — which the admin reset already serves.

## Why

Recording is nearly free and closes the zero-forensic-trace hole. Locking would hand any visitor a denial-of-service button against an app where every unlock requires the one human admin.

## Reversibility

yes — a lockout policy can be added later, and the recorded failures are exactly the data that decision would need

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-LOCKOUT-01`, which is marked RULED in Article X with a pointer here.*
