# SW-ADR-062 — Structured JSON logs, level from LOG_LEVEL

| Field | Value |
|---|---|
| ADR | `SW-ADR-062` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-005` |

## Context

SW-ADR-005's four words 'structured logs to stdout' are the entire specification. 'Structured' is not a format, and uvicorn's access logger and the application logger emit in two different shapes unless something reconciles them.

## Options considered

- A. JSON lines, a fixed required field set, LOG_LEVEL defaulting to INFO, uvicorn's loggers reconfigured onto the same handler.
- B. Human-readable lines.
- C. JSON deployed, human-readable locally.

## Decision

**A. Required fields: timestamp, level, message, request_id, route, method, status, duration_ms, user_id (nullable), revision.**

## Consequences

- Without a level variable, diagnosing the deployed environment means rebuilding and redeploying — and every deploy is an outage under the single-host-port topology.
- The format sample belongs in the PRD so the client can build their log-group queries before the first deploy.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
