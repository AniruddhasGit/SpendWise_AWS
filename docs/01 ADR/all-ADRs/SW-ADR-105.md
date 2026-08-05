# SW-ADR-105 — A closed allowlist of nine audit actions, with typed detail shapes

| Field | Value |
|---|---|
| ADR | `SW-ADR-105` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-AUDIT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-AUDIT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-AUDIT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Nine action types, each with a Pydantic-validated `details` shape: `password_reset_issued` {target_user_id} · `sessions_revoked` {target_user_id, count} · `user_deactivated` {target_user_id} · `user_reactivated` {target_user_id} · `role_changed` {target_user_id, old_role, new_role} · `bootstrap_admin_claimed` {user_id} · and three **read-audit** types with empty details: `users_list_viewed`, `sessions_list_viewed`, `audit_log_viewed` — one row per request to each admin endpoint that exposes other users' data. **Prohibited in `details` under any type**, enforced by the schemas: tokens or token hashes, password material, amounts, descriptions, receipt keys, free text. An action type not on the list cannot be written.

## Why

The rows are permanent, so an unconstrained JSONB is an irreversible leak channel — one 'reset issued' row carrying the token would undo `§10.7` forever, and one 'what changed' blob with an amount would breach `§4.5` through the log. A closed allowlist with typed shapes makes both structurally impossible.

## Reversibility

**NO** for rows once written — which is exactly why the allowlist is ruled before the first row exists

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-AUDIT-01`, which is marked RULED in Article X with a pointer here.*
