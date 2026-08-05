# Error code registry — GENERATED from contract.json. DO NOT HAND-EDIT.

`SW-ADR-051` states in its own Consequences that *"a stable `code` is the only thing
that lets the PRD write a binary acceptance criterion for an error path, which the
Definition of Done requires."* The registry that makes that true was never written, so
`CONSTITUTION.md` Art IX.3 could not be met on any error path. `SW-ADR-138` writes it.

**Envelope.** `{"error": {"code": "...", "message": "...", "field": "..."}}`

`field` carries the CLIENT's name for the input - `amount`, never `amount_paise`.

| `code` | Status | Carries `field` | When |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | yes | any input fails a stated rule |
| `NOT_FOUND` | 404 | no | not-yours or not-found, on every verb (P-PRV-03) |
| `UNAUTHENTICATED` | 401 | no | no credential presented |
| `SESSION_INVALID` | 401 | no | credential presented but revoked, expired, idle-timed-out or signed with a rotated secret |
| `ACCOUNT_DEACTIVATED` | 401 | no | valid session, is_active false |
| `FORBIDDEN` | 403 | no | authenticated but the role does not hold the capability |
| `EMAIL_TAKEN` | 409 | yes | registration against an existing address, subject to SW-ADR-102's enumeration posture |
| `CONFLICT` | 409 | yes | duplicate category name; last-administrator guard |
| `RATE_LIMITED` | 429 | no | a rate limit is hit; carries Retry-After |
| `BAD_REQUEST` | 400 | no | malformed body that never reaches validation |
| `INTERNAL` | 500 | no | unhandled; the message is generic and never carries detail |

**A code not on this list cannot be returned.** The list is closed, in the same way
the audit-log action allowlist is closed (`SW-ADR-105`): an unlisted value is a defect,
not an extension point.
