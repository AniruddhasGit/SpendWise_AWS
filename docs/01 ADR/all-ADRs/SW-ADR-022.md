# SW-ADR-022 — Sessions are revocable: a database row plus the token's jti claim

| Field | Value |
|---|---|
| ADR | `SW-ADR-022` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S5` |

## Context

SRC-001 S5 records the client's reasoning in full: a stateless token cannot answer 'who is signed in', cannot be revoked on sign-out, and cannot be killed when an admin resets a password.

## Options considered

- A. Stateless JWT only.
- B. A sessions table whose row id is carried in the token's jti claim, checked on every request.

## Decision

**B. Every request resolves the jti to a session row and confirms it exists and is not revoked.**

## Consequences

- The JWT's statelessness is deliberately given up. What it still buys is cheap signature rejection of garbage tokens before the database is touched.
- last_seen_at is bumped at most once a minute. The throttle compares the timestamp on the row ALREADY fetched - no in-process state, so it behaves identically across 2 uvicorn workers and N tasks.
- Active means last_seen_at within 15 minutes and revoked_at null (SRC-001 S5.3).
- An admin password reset revokes every session of that user in the same transaction. A reset that leaves the old session working is not a reset (SRC-001 S5.5).
- OPEN-SESSION-01: SRC-001 defines no token lifetime or absolute session cap. Proposed - 30-day absolute, 14-day idle for users, 30-minute idle for admins, id rotated on privilege change. NOT YET RULED.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
