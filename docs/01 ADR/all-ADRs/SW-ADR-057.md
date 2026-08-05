# SW-ADR-057 — The SPA handles 401 through one interceptor, and never renders zeros for absent data

| Field | Value |
|---|---|
| ADR | `SW-ADR-057` |
| Pack | `SPENDWISE_V1` |
| Type | UX_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §5.4` · `SRC-001 §7.4` |

## Context

SRC-001 §5.4 guarantees a user's token can die WHILE they are using the app — admin force-sign-out and admin password reset both revoke sessions instantly. Nothing specifies the client half. The dashboard fires at least two calls, so a naive per-call handler redirects twice.

## Options considered

- A. One response interceptor: on 401 clear client state, route to sign-in with a reason banner, suppress duplicate redirects.
- B. A re-authenticate modal preserving input.
- C. Per-call handling.

## Decision

**A, with the in-progress add-expense draft held in memory so B can be added later without rework.**

## Consequences

- Separately and non-negotiably: a failed request renders an error state with a retry, NEVER zeros. In a money app a rendered 0.00 from a failed call is indistinguishable from a true zero.
- SRC-001 §7.4's one-call dashboard means one failure blanks everything, so the error state is not an edge case.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
