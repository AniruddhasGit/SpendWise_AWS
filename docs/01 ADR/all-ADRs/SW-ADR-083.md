# SW-ADR-083 — The audit log carries no foreign keys

| Field | Value |
|---|---|
| ADR | `SW-ADR-083` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-031` |
| Raised by | QA FINDING-18 (MEDIUM) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-031` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-031` made the audit log immutable via a REVOKE plus a trigger that raises on UPDATE and DELETE. If `admin_audit_log` also carried foreign keys to `users`, a referential action would fire that trigger and abort the user deletion — so `SRC-001 §6.9` ("cascades to categories, expenses and sessions… does **not** cascade to the audit log, because the whole point is that it survives") would be unsatisfiable in both directions at once.

## Decision

**`admin_audit_log.admin_id` and `admin_audit_log.target_user_id` carry **no foreign key**. They are plain BIGINT columns holding ids that may no longer resolve.**

## Consequences

- The only design that satisfies both halves of `SRC-001 §6.9`. It was stated nowhere before this record.
- Consequence accepted: the log can reference a deleted user. That is the intent — the log outlives its subjects.
- `SW-ADR-031`'s immutability stands unchanged.

---

*A superseding record, not an edit. `SW-ADR-031` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
