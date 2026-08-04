# SW-ADR-001 — Governance: one person holds every approver role

| Field | Value |
|---|---|
| ADR | `SW-ADR-001` |
| Pack | `SPENDWISE_V1` |
| Type | GOVERNANCE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §1` · `SRC-002 §2` |

## Context

SpendWise is a personal project. The delivery method this project borrows assumes the builder is never the decider, because the whole point of a decision register is to make a decision *queue* visible. Here one person is client, money-signer and rules-signer.

## Options considered

- A. The client holds all three roles.
- B. The client decides product; a named other person signs money.
- C. A third-party stakeholder decides and the client builds.

## Decision

**A. The client is sole decider, money-signer, and the person who signs CONSTITUTION.md.**

## Consequences

- The method's central control WEAKENS: a decider who can answer instantly never feels the queue the register exists to make visible.
- Compensating control adopted with this ruling: every decision classed IRREVERSIBLE gets a fresh zero-context second opinion before it is acted on. That substitutes for the missing second human.
- What survives is the written answer, the reversibility class, and the kill condition. What is lost is the natural delay that catches a bad answer before it is built on.
- The client's exact full name for the signature line is OPEN-NAME-01. A name inferred from a git identity is not a signature.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
