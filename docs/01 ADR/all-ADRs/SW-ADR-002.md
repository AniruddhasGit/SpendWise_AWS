# SW-ADR-002 — Greenfield: nothing is being replaced

| Field | Value |
|---|---|
| ADR | `SW-ADR-002` |
| Pack | `SPENDWISE_V1` |
| Type | SCOPE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §3` |

## Context

The delivery approach differs sharply for greenfield, brownfield, rescue and migration work. Each puts the risk somewhere different and needs a different day-one proof. Choosing wrong does not announce itself.

## Options considered

- A. Clean slate - nothing exists.
- B. A spreadsheet or manual process is being replaced.
- C. An existing application is being replaced.

## Decision

**A. Clean slate. Nothing exists that SpendWise replaces.**

## Consequences

- No data migration, no parity harness, no dual-running, nothing to switch off. Cutover is genuinely lighter than a replacement project's.
- COST: with no prior system or spreadsheet, NO source document exists for any requirement. Everything traces to SRC-001 and nothing else, which makes that one file the single point of failure for the whole specification.
- Corroborating machine check: D:\Project\SpendWise was an empty directory with no git repository, observed 2026-08-05. That proves no CODE existed; the client's answer is what establishes no process exists elsewhere.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
