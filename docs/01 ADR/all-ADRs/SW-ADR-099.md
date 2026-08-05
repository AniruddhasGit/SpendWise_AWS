# SW-ADR-099 — Session and token lifetimes

| Field | Value |
|---|---|
| ADR | `SW-ADR-099` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-SESSION-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-SESSION-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-SESSION-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Absolute cap 30 days. Idle expiry 14 days for `user`, **30 minutes for `admin`**. The JWT carries `exp` = issue + 30d. `sessions` gains `expires_at TIMESTAMPTZ NOT NULL` **in the first migration, before any data exists**. `get_current_user` rejects when now > `expires_at`, when idle exceeds the role's window, or when revoked. All four numbers live in settings and `.env.example`.

## Why

Ordinary numbers that close the eternal-token-on-plain-HTTP hole. The column must exist now because adding `expires_at` after real rows exist means backfilling a security semantic.

## Reversibility

yes — numbers in settings; the column is additive

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-SESSION-01`, which is marked RULED in Article X with a pointer here.*
