# SW-ADR-064 — The build version comes from a Docker ARG and is never silently a placeholder

| Field | Value |
|---|---|
| ADR | `SW-ADR-064` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-005` · `SRC-001 §7.7` |

## Context

SW-ADR-005 requires a health endpoint reporting build and schema version. Nothing says where the build string comes from, and there is no CI to inject one. A build string defaulting to 'dev' or 'unknown' in the deployed image is a failure mode that surfaces only when it is needed.

## Options considered

- A. A Docker ARG/ENV BUILD_VERSION passed as the git SHA at build time, reported by /readyz with the boot-cached Alembic revision.
- B. A generated _version.py.
- C. Read the image tag at runtime.

## Decision

**A. An unset BUILD_VERSION reports the literal string `unset` and logs one WARN at boot.**

## Consequences

- 'Which image is running right now' is the first question of every incident and the only way to confirm a rollback took effect.
- /healthz stays a bare OK per SRC-001 §7.7 — the version detail lives on /readyz.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
