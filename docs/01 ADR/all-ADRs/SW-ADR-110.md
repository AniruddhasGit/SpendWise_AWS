# SW-ADR-110 — The reset code is redeemed on the sign-in page

| Field | Value |
|---|---|
| ADR | `SW-ADR-110` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-RESETUI-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-RESETUI-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-RESETUI-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

A third mode on the sign-in page — no new route. 'Have a reset code?' switches to email + code + new password. Four outcome states, each with its own message: **invalid** ('This reset code is not recognised.'), **already used** ('This reset code has already been used — ask your administrator for a new one.'), **expired** ('This reset code has expired — ask your administrator for a new one.'), **success** ('Password updated — sign in with your new password.', returning to sign-in; no auto-login). Separately: `/admin/audit` stands as a sub-view — `§9.3`'s 'Plus the audit log' is the client's own text, so the sub-route is presentation, not scope.

## Why

Built literally, the locked-out user — the persona the admin role exists for — receives a code and a dead end. The sign-in page is where a signed-out person already is. Distinguishing used from expired from invalid helps the legitimate holder and tells an attacker nothing useful: a used code is spent, an expired one is dead.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-RESETUI-01`, which is marked RULED in Article X with a pointer here.*
