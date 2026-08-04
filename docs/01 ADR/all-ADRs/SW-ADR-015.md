# SW-ADR-015 — Standing delegation of technical decisions to the build session

| Field | Value |
|---|---|
| ADR | `SW-ADR-015` |
| Pack | `SPENDWISE_V1` |
| Type | GOVERNANCE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §16` |

## Context

The client instructed, verbatim: 'if you get any questions make decisions as this is a practice app.' The client's explicit instruction is first in the precedence order, but the reserved matters exist precisely because a model deciding them IS the failure mode. A blanket delegation would quietly repeal the constitution being adopted.

## Options considered

- A. Full delegation - the build session decides everything.
- B. Delegation with the reserved floor intact.
- C. No delegation.

## Decision

**B. Technical questions are the build session's; the reserved floor holds.**

## Consequences

- TECHNICAL questions - decided by the build session, each logged as one JUDGMENT CALL line carrying what would make it wrong. No interruption.
- REVERSIBLE RESERVED matters - decided by the build session, applied immediately, and BATCHED into a digest for the client to confirm or reverse. They move at the speed of a decision, not of a meeting.
- RESERVED AND IRREVERSIBLE - money above a ceiling, deleting data, anything public or outward-facing, anything marked [HUMAN] - still stops and waits. No delegation reaches these.
- RISK CREATED: under-escalation, which the escalation floor cannot see by itself. At every gate a fresh non-author session samples the JUDGMENT CALL log and asks 'should this have gone to the human?'. The rate is recorded.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
