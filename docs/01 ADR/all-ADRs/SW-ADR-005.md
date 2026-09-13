# SW-ADR-005 — The build session writes application code only and touches no AWS

| Field | Value |
|---|---|
| ADR | `SW-ADR-005` |
| Pack | `SPENDWISE_V1` |
| Type | DELIVERY_MODEL |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §1` · `SRC-002 §6` · `SRC-001 E-5` |
| Superseded by | `SW-ADR-155` (2026-09-13) |

## Context

The client intends to build DEV, UAT and PROD by hand, in the AWS console, deliberately, in order to practise the DevOps role. That places the deployment half of the system outside the build session's reach.

## Options considered

- A. The build session writes CI/CD and the client wires AWS.
- B. The build session writes application code only; the client builds ALL infrastructure and pipelines by hand.
- C. The build session does everything including AWS.

## Decision

**B. No pipeline files, no infrastructure-as-code, nothing created in AWS by the build session.**

## Consequences

- In exchange the build session owes three things: (1) code that is already AWS-shaped; (2) ADVANCE notice of every AWS dependency, early enough to prepare while code is still being written; (3) documents written so that 'a human did this by hand' is indistinguishable from 'a pipeline did this'.
- Obligation (3) costs nothing, because every piece of evidence in this method is already 'here is the command I ran and here is the output I saw', never 'the pipeline went green'.
- RISK: the build session will NEVER observe the app running in any AWS environment. Every claim it makes about AWS behaviour is REASONED, not observed, and must be labelled that way under Art III.1. Only the client can convert those claims into evidence.
- AWS-shaped means: all configuration through environment variables; nothing written to local disk that must survive a restart; a health endpoint reporting build and schema version; structured logs to stdout; graceful shutdown on SIGTERM; migrations a separate runnable step, never done on boot.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
