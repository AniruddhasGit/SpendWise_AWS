# SW-ADR-063 — A log deny-list, red-proofed

| Field | Value |
|---|---|
| ADR | `SW-ADR-063` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-012` · `SW-ADR-005` |

## Context

Nothing says what must never appear in a log line. This application handles several things whose entire security model is that they are seen once: the admin-issued reset token, the session JWT, the five-minute presigned URL (itself a bearer credential for a receipt image), and DATABASE_URL, which contains the database password. FastAPI's default 422 echoes the offending input back — which for login and reset-completion means the submitted password or token.

## Options considered

- A. A named deny-list enforced by a logging filter, secrets redacted in the settings repr, and 422 bodies never logged verbatim.
- B. Reviewer discipline.

## Decision

**A. Deny-list: password, password_hash, Authorization and Cookie headers, token, token_hash, presigned URL query strings, DATABASE_URL, JWT_SECRET.**

## Consequences

- A reset token in a log line defeats the entire out-of-band handover SW-ADR-012 was designed around.
- RED-PROOFED, per the same discipline applied to RLS: plant each value, run the request, assert it is absent from the captured output. A filter nobody has watched catch something is decoration.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
