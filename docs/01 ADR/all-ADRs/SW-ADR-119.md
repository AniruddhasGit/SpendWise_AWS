# SW-ADR-119 — Every destructive action confirms, naming the blast radius

| Field | Value |
|---|---|
| ADR | `SW-ADR-119` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-DESTRUCT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-DESTRUCT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-DESTRUCT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

No undo exists in v1, so the confirm is the protection. Delete category — 'Delete {name}? {n} expenses will become uncategorised.' ('No expenses use this category.' when 0). Delete expense — 'Delete this expense of Rs{amount} on {date}?' plus 'Its receipt will also be deleted.' when one is attached. Remove receipt — 'Remove this receipt? This cannot be undone.' Revoke sessions — 'Sign {user} out of {n} active sessions?' Deactivate — 'Deactivate {email}? They will be signed out immediately and cannot sign in until reactivated.' Role change — 'Demote {email} to user? Their sessions end immediately.' Reset — 'Issue a password reset for {email}? All their sessions will end.' **No type-the-name friction anywhere** — overkill at this scale.

## Why

Deleting a category silently strips categorisation from every expense that used it. Naming the count makes the consequence visible at the moment of choice, which is the cheapest possible substitute for undo.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-DESTRUCT-01`, which is marked RULED in Article X with a pointer here.*
