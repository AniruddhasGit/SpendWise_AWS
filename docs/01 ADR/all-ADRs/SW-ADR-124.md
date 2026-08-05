# SW-ADR-124 — The restore runbook is written before it is needed

| Field | Value |
|---|---|
| ADR | `SW-ADR-124` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-RESTORE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-RESTORE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-RESTORE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

`docs/30 Deployment/RESTORE_RUNBOOK.md` — a document, inside the build session's boundary. Contents ruled: (1) RDS point-in-time restore creates a **new instance with a new endpoint** — restore -> update `DATABASE_URL` in SSM -> force new ECS deployment -> verify -> delete the old instance promptly; a brief two-instance overlap during cutover is hours, accepted and named. (2) **S3 is not in the snapshot** — after a restore, `receipt_key` values may reference objects deleted after the restore point; the app treats a missing object as a graceful 'Receipt no longer available', no reconciliation job in v1. (3) One client-executed restore drill against the non-live database before go-live, evidence being the client's own report.

## Why

Restore is a one-way door executed under pressure, and the prep queue already promises a drill against a checklist that does not exist. Every claim in it is reasoned, not observed, and labelled so.

## Reversibility

yes — it is paper until the day it is not, which is the point of writing it early

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-RESTORE-01`, which is marked RULED in Article X with a pointer here.*
