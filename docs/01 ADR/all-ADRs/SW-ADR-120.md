# SW-ADR-120 — One task, min-healthy 0, expand-contract migrations

| Field | Value |
|---|---|
| ADR | `SW-ADR-120` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-DEPLOY-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-DEPLOY-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-DEPLOY-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

The ECS service runs one task with deployment configuration **minimum-healthy 0% / maximum 100%**; every deploy is a hard downtime window of roughly stop + boot + migration time, accepted and documented — and that environment is never called production. Standing rule adopted: **expand-contract** — a migration shipped with a release may only add or otherwise stay compatible with the previous image; destructive changes wait one release. Image rollback is therefore always safe against the current schema. The client must set min-healthy 0 or the first redeploy deadlocks on the host port. *(Reasoned, not observed.)*

## Why

With one instance and one fixed host port, two tasks cannot coexist, so zero-downtime deploys are structurally unavailable — pretending otherwise is the only wrong answer. Expand-contract is what makes boot-time migrations plus rollback jointly safe.

## Reversibility

yes — process rules

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-DEPLOY-01`, which is marked RULED in Article X with a pointer here.*
