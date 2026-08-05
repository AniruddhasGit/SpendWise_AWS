# SW-ADR-049 — BOOTSTRAP_ADMIN_EMAIL is evaluated only when zero admins exist, and startup fails without it

| Field | Value |
|---|---|
| ADR | `SW-ADR-049` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-021` · `SRC-001 §4.4` |

## Context

SW-ADR-021 gated the first-admin claim and stopped there. Unset on a fresh database means nobody can claim it and, since only an existing admin may promote, the deployment is permanently adminless with no recovery. Evaluated on every registration instead of only at zero admins, it becomes a standing privilege-escalation channel through a task definition the client edits often.

## Options considered

- A. Evaluate only when the admin count is zero; match case-insensitively; abort startup if unset while no admin exists.
- B. Warn and continue.
- C. Evaluate on every registration.

## Decision

**A.**

## Consequences

- Turns an unrecoverable state into a five-second one, and matches the fail-fast configuration rule.
- Closes the edge cases SW-ADR-021 left open.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
