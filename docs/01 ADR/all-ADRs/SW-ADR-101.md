# SW-ADR-101 — The role is re-read, never trusted from the token

| Field | Value |
|---|---|
| ADR | `SW-ADR-101` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-ROLECHG-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-ROLECHG-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-ROLECHG-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Authorization re-reads the role from the user row `get_current_user` already loads — zero extra queries. On demotion admin→user: every session of the target revoked in the same transaction, audit-logged. On promotion: sessions kept; the new role takes effect on the next request via the re-read.

## Why

Re-reading makes the security-critical direction instant even if revocation raced. Revoking on demotion only avoids punishing a promotion with a logout. A demoted admin retains nothing for even one request.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-ROLECHG-01`, which is marked RULED in Article X with a pointer here.*
