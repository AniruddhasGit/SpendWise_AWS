# SW-ADR-029 — The money column is amount_paise; currency is NOT NULL on both tables

> **⚠ AMENDED 2026-08-05.** This record said the erratum was an "erratum candidate".
> A candidate is not a filing. **`ERRATUM E-9` is now actually filed** against `SRC-001 §6.6`.

| Field | Value |
|---|---|
| ADR | `SW-ADR-029` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.6` · `SW-ADR-013` |

## Context

SRC-001 §6.6 names the column `amount_cents` while SW-ADR-013 fixed the product at Indian Rupees, whose minor unit is the paisa. SW-ADR-013 also added a currency column to expenses without stating its nullability or default.

## Options considered

- A. Rename to `amount_paise`; currency NOT NULL DEFAULT 'INR' with a CHECK, on both users and expenses.
- B. Keep `amount_cents` for fidelity to SRC-001.

## Decision

**A. `amount_paise`, and currency NOT NULL DEFAULT 'INR' CHECK (currency = 'INR') on both tables.**

## Consequences

- A column named `cents` holding paise is a comment that lies, and the whole point of SW-ADR-013 was that money must not be silently reinterpreted.
- The CHECK is deliberately narrow: widening it later is one migration, whereas discovering a JPY row with two implied decimals is unrecoverable.
- Filed as an erratum candidate against SRC-001 §6.6.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
