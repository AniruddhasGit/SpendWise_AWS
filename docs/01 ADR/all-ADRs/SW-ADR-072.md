# SW-ADR-072 — The category foreign key: referential actions, stated

| Field | Value |
|---|---|
| ADR | `SW-ADR-072` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-035` |
| Raised by | QA FINDING-3 (CRITICAL) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-035` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-035`'s composite FK is correct in principle — FK checks bypass RLS, so only the database can stop a cross-user category reference. But no referential action was stated, and `ON DELETE SET NULL` on a composite key nulls **every** referencing column including `user_id`, which is `NOT NULL`. The column-list form `ON DELETE SET NULL (category_id)` requires PostgreSQL 15, and **no document pins a version** — the prep queue still asks the client which one they will create.

## Decision

**`ON DELETE NO ACTION`, with the expenses service performing an explicit `UPDATE expenses SET category_id = NULL WHERE category_id = :id` inside the same transaction as the category delete. No PostgreSQL version floor is required.**

## Consequences

- Satisfies `SRC-001 §7.2` — deleting a category nulls `category_id` and leaves the expenses alone — without depending on a version nobody has chosen.
- `SRC-001 §3.4`'s module rule already forces this through the expenses service, so the code path exists regardless.
- Every other foreign key in the schema must also state its action explicitly. Zero ADRs did before this one; `SW-ADR-083` covers the audit log, and the data model must state the rest.

---

*A superseding record, not an edit. `SW-ADR-035` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
