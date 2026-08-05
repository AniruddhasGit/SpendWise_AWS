# SW-ADR-051 — One error envelope for every non-2xx response

| Field | Value |
|---|---|
| ADR | `SW-ADR-051` |
| Pack | `SPENDWISE_V1` |
| Type | API_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.10` · `SRC-001 §10.1` |

## Context

No error shape is defined anywhere. SRC-001 §10.10 fixes only schema validation, which yields FastAPI's default 422. Every hand-raised refusal — a bad reset token, a last-admin guard, a revoked session — would arrive in a different shape, so the SPA cannot render any of them generically and falls back to 'Something went wrong' for everything.

## Options considered

- A. `{error: {code, message, field?}}` on every non-2xx, with a stable machine `code`, including a rewritten 422.
- B. RFC 7807 problem+json.
- C. Keep FastAPI's default.

## Decision

**A.**

## Consequences

- A stable `code` is the only thing that lets the PRD write a binary acceptance criterion for an error path, which the Definition of Done requires.
- 422 must be rewritten into the envelope, and its `field` reported using the CLIENT's field name (rupees) rather than the converted one (paise), or the error cannot be anchored to the input the user typed.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
