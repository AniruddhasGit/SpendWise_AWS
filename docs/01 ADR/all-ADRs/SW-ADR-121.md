# SW-ADR-121 — Forward-only for anything destructive

| Field | Value |
|---|---|
| ADR | `SW-ADR-121` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-DOWNGRADE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-DOWNGRADE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-DOWNGRADE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

A migration ships a working `downgrade()` **only** when it is mechanically trivial and destroys nothing. Any migration whose downgrade would lose data implements `downgrade()` as `raise NotImplementedError("Forward-only: rollback is restore-from-backup — see RESTORE_RUNBOOK")`. The migration template states this. **Up/down/up on an empty schema is never claimed as evidence beyond DDL syntax.** The real rollback story is expand-contract plus RDS point-in-time restore.

## Why

A `downgrade()` that has never run against populated data is decoration, which Art VII.1 forbids. Stating restore-from-backup plainly is the honest version of the same promise.

## Reversibility

yes — the policy exists to prevent irreversible loss

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-DOWNGRADE-01`, which is marked RULED in Article X with a pointer here.*
