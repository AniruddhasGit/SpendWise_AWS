# SW-ADR-122 — Opportunistic pruning of dead auth rows at login

| Field | Value |
|---|---|
| ADR | `SW-ADR-122` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-PRUNE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-PRUNE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-PRUNE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

At successful login, bounded to **1,000 rows per table per occasion**: delete `sessions` rows dead >=90 days (revoked or expired more than 90 days past) and `password_resets` rows used or expired >=90 days ago. **The audit log is never pruned** — that stands absolutely. The 90-day figure lives in settings.

## Why

`sessions` gains a row per login and never loses one, on 20 GB with autoscaling deliberately off — unbounded growth is the alternative. Ninety days keeps a generous forensic window, and the failed-login log lines carry the attack record anyway.

## Reversibility

**NO** for any individual deleted row — bounded by pruning only rows already dead 90 days, which is why the window is wide and configurable

> **⚠ IN THE CLIENT DIGEST.** Ruled under the escalation grant; one message reverses it.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-PRUNE-01`, which is marked RULED in Article X with a pointer here.*
