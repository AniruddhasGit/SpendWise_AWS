# SW-ADR-048 — Client IP comes from the socket unless a trusted proxy is declared

| Field | Value |
|---|---|
| ADR | `SW-ADR-048` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.3` · `SRC-001 §10.9` · `SW-ADR-014` |

## Context

Nothing says where the client IP comes from, for either the rate limiter's key or sessions.ip. Trusting X-Forwarded-For unconditionally makes the per-IP rate limit a no-op and fills sessions.ip with attacker-chosen strings an admin will read as fact.

## Options considered

- A. Socket peer by default; trust forwarded headers only when TRUSTED_PROXY_COUNT is set.
- B. Socket peer only.
- C. Trust the header when present.

## Decision

**A. Default unset, therefore fail-closed.**

## Consequences

- B is correct TODAY precisely because SW-ADR-014 removed the load balancer — and becomes silently wrong the moment the client adds one during their DevOps practice. Nothing would announce that transition.
- The env-gated form stays correct through the client's planned infrastructure changes and matches the fail-fast configuration pattern already required.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
