# SW-ADR-087 — Receipt replacement: commit first, delete after

| Field | Value |
|---|---|
| ADR | `SW-ADR-087` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-037` |
| Raised by | QA FINDING-24 (LOW) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-037` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-037` said a replaced receipt object is deleted from S3 "in the same operation". S3 is not in the database transaction, so that is not achievable and the ordering was unspecified. Delete-then-rollback leaves a row pointing at a vanished object; the reverse leaves an orphan.

## Decision

**Commit the row first, then delete the previous object on a best-effort basis. On delete failure, log it and leave the orphan for the lifecycle rule.**

## Consequences

- Silent loss of a user's receipt image is unrecoverable and invisible until they click view. An orphan is merely storage.
- The orphan path is folded into `OPEN-S3LIFE-01` rather than pre-decided here — object deletion is irreversible and the expiry window is the client's to name.

---

*A superseding record, not an edit. `SW-ADR-037` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
