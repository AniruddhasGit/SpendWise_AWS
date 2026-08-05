# SW-ADR-076 — Timestamp nullability, per column

| Field | Value |
|---|---|
| ADR | `SW-ADR-076` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-024` |
| Raised by | QA FINDING-10 (HIGH) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-024` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-024` ruled "all timestamps TIMESTAMPTZ **NOT NULL** DEFAULT now()". Taken literally that makes `sessions.revoked_at` non-null at insert — so every session is born revoked — and `password_resets.used_at` non-null, so every token is born used. `SW-ADR-039`, written in the same pass, indexes `revoked_at IS NULL`: an index over a condition its sibling made unsatisfiable. The ADR's claim of eleven timestamp columns was also wrong; there are ten.

## Decision

**TIMESTAMPTZ in UTC everywhere, with nullability stated per column: `NOT NULL DEFAULT now()` for `users.created_at`, `sessions.issued_at`, `sessions.last_seen_at`, `categories.created_at`, `expenses.created_at`, `admin_audit_log.created_at`; `NOT NULL` with no default for `password_resets.expires_at`; **NULLABLE, no default** for `sessions.revoked_at`, `password_resets.used_at`, `expenses.updated_at`.**

## Consequences

- Ten columns, enumerated. The miscount in `SW-ADR-024` is why they are now listed rather than described.
- `SRC-001 §5.3`'s definition of an active session — `revoked_at is null` — becomes satisfiable, and `SW-ADR-039`'s partial index becomes meaningful.
- `spent_on` remains a DATE, per `SW-ADR-024`, which was right about that.

---

*A superseding record, not an edit. `SW-ADR-024` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
