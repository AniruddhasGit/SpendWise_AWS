# SW-ADR-127 — A container health check and a running-task alarm

| Field | Value |
|---|---|
| ADR | `SW-ADR-127` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-MONITOR-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-MONITOR-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-MONITOR-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Both, free tier: (1) an ECS task-definition health check on `/healthz` — `CMD-SHELL curl -f http://localhost:{port}/healthz || exit 1`, interval 30s, timeout 5s, retries 3, **startPeriod 120s** sized to cover boot-time migrations — so ECS itself restarts an unhealthy task. (2) A CloudWatch alarm on the service's `RunningTaskCount < 1` for 2 consecutive minutes, notifying an SNS topic with the client's email subscribed. **Beyond those two, 'the client is the monitor' is accepted explicitly** as the recorded posture — no external uptime pinger in v1. Both are prep-queue rows, and the alarm must be forced once to prove it fires. *(Reasoned, not observed.)*

## Why

`/healthz` exists because a load balancer would call it, and `SW-ADR-014` removed the load balancer — this gives it its two callers back at zero cost. The alternative on offer is discovering downtime by visiting the site.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-MONITOR-01`, which is marked RULED in Article X with a pointer here.*
