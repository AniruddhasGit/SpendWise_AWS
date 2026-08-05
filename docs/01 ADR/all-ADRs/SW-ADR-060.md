# SW-ADR-060 — A committed .env.example is the environment-variable manifest

| Field | Value |
|---|---|
| ADR | `SW-ADR-060` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §11.4` · `SRC-001 §8.4` · `SW-ADR-005` |

## Context

The variable names are scattered across four documents and no file enumerates them. The client hand-types every SSM parameter with no pipeline to validate them; a missing name is a crash loop with no load balancer to report it, and a MISSPELLED optional one is worse — S3_BUCKET is optional, so one typo ships a deployment where receipts are silently dead and startup is green.

## Options considered

- A. A committed .env.example that is the single manifest, each line annotated required/optional and its default.
- B. The BaseSettings class is the manifest.
- C. Leave scattered.

## Decision

**A.**

## Consequences

- B was rejected because it makes the client read Python to configure AWS, which breaks SW-ADR-005's bargain that documents never assume automation.
- Any variable whose absence DEGRADES rather than aborts — today only S3_BUCKET — logs one WARN at startup naming the disabled feature.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
