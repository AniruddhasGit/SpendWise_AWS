# SW-ADR-039 — Index set beyond SRC-001 §6.8

| Field | Value |
|---|---|
| ADR | `SW-ADR-039` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.8` · `SRC-001 §7.6` |

## Context

§6.8 names four indexes. Several access paths the API requires have none.

## Options considered

- A. Add the indexes the stated endpoints need.
- B. Ship §6.8's four and add more when something is slow.

## Decision

**A. Added: unique lower(email) on users; unique (id, user_id) on categories; unique (user_id, lower(name)) on categories; (user_id) on categories; (revoked_at) partial where null on sessions; (user_id, expires_at) on password_resets; (admin_id, created_at DESC) and (target_user_id) on admin_audit_log.**

## Consequences

- Every one traces to a query the API contract requires, not to speculation.
- Index cost is write amplification on a free-tier instance; the set is deliberately small.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
