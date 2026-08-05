# SW-ADR-126 — CloudWatch Logs, 30-day retention

| Field | Value |
|---|---|
| ADR | `SW-ADR-126` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-LOGS-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-LOGS-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-LOGS-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Prep-queue row added: the client creates log group `/ecs/spendwise` with **retention set at creation**, wires the task definition to the `awslogs` driver targeting it (auto-create off), and grants the execution role `logs:CreateLogStream` and `logs:PutLogEvents`. **Default retention 30 days.** Needed by the first deploy — before it, a crash loop destroys its own record.

## Why

With the default driver, logs die with every task, so the evidence of a crash is destroyed by the restart it causes. Thirty days at hobby volume sits well inside the free tier while the retention figure remains a cost dial.

## Reversibility

yes — retention changes in one console action

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-LOGS-01`, which is marked RULED in Article X with a pointer here.*
