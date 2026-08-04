# SW-ADR-012 — Password reset is admin-issued only in v1

| Field | Value |
|---|---|
| ADR | `SW-ADR-012` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT_SCOPE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S7.1` · `SRC-001 S5.5` · `SRC-001 E-3` |

## Context

SRC-001 S7.1 lists a user-facing 'request a password reset with a token' endpoint, but S2 contains no email infrastructure of any kind - no SES, no SMTP. A self-service token has no delivery route.

## Options considered

- A. Admin-issued only; token handed over out-of-band.
- B. Add SES and keep self-service reset.
- C. Display the token on screen to the requester.

## Decision

**A. Only an admin can issue a reset. No self-service 'forgot password' endpoint or button exists in v1.**

## Consequences

- REMOVED FROM SCOPE: the user-facing request-a-reset endpoint.
- RETAINED: admin issues the reset; the token is shown to the admin once; single-use; hashed at rest; one-hour expiry; and EVERY session of that user is revoked in the same transaction (SRC-001 S5.5).
- Option C was rejected outright - it would let anyone reset anyone's password.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
