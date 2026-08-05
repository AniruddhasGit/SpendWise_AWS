# SW-ADR-123 — A staging prefix with a one-day expiry

| Field | Value |
|---|---|
| ADR | `SW-ADR-123` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-S3LIFE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-S3LIFE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-S3LIFE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

The presigned POST targets `staging/{user_id}/{uuid}.{ext}`. Attach verifies the staging prefix matches the caller, server-side copies to the permanent `receipts/{user_id}/{expense_id}/{uuid}.{ext}` (the `§8.3` shape is preserved), then deletes the staging object. **One client-created S3 lifecycle rule: expire objects under `staging/` after 1 day** — abandoned uploads self-destruct in 24 hours. On expense delete: best-effort object delete after commit; a failed delete logs and leaves an orphan under `receipts/`, accepted as storage-only cost at personal scale. No S3 versioning in v1.

## Why

The presigned design means the browser writes before the server knows the key exists, so unattached objects are otherwise permanently unenumerable. A lifecycle rule cannot distinguish orphaned from live objects under `receipts/`, and pretending otherwise would be decoration.

## Reversibility

partly — prefixes and windows change freely; expired objects are gone, which is the intent

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-S3LIFE-01`, which is marked RULED in Article X with a pointer here.*
