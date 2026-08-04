# SW-ADR-006 — Commercial machinery cut; every quality control kept

| Field | Value |
|---|---|
| ADR | `SW-ADR-006` |
| Pack | `SPENDWISE_V1` |
| Type | PROCESS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §7` |

## Context

Much of the borrowed delivery method assumes a consultancy billing a client. Waiving a quality check is a reserved matter, so which parts are dropped cannot be decided by the build session.

## Options considered

- A. Cut the commercial machinery only.
- B. Keep everything, with a charter replacing the contract.
- C. Cut hard - day-one gate, spec rows and checkers only.

## Decision

**A. Cut the money machinery. Keep every quality control.**

## Consequences

- CUT: paid scoping agreement, contract, pricing, invoice schedule, checkpoints-as-invoices.
- KEPT IN FULL: the decision ledger and its clocks; the OPEN register; the day-one proof; acceptance criteria that are binary and testable; the zero-guess design freeze; fresh-agent adversarial review; red-proofing on a schedule; the cross-user isolation adversary; the deployment runbook discipline; the closing harvest.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
