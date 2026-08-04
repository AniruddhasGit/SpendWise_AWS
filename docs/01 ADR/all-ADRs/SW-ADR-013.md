# SW-ADR-013 — Indian Rupees only; integer paise; currency snapshotted onto each expense

| Field | Value |
|---|---|
| ADR | `SW-ADR-013` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S6.1` · `SRC-001 S6.2` · `SRC-001 S6.6` · `SRC-001 E-7` |

## Context

SRC-001 S6.2 puts a currency column on users but S6.6 has none on expenses, so changing currency would silently reinterpret every historical row. 'Cents' also assumes two decimal places, which is wrong for JPY (0) and KWD (3).

## Options considered

- A. INR only, two decimals.
- B. User-selectable currency from a 2-decimal allowlist.
- C. Full multi-currency with exchange rates.

## Decision

**A. v1 supports INR only. Amounts stored as integer paise. Display rounds to two decimals.**

## Consequences

- The currency column on users becomes a constant rather than a choice. It is KEPT rather than dropped - removing it costs nothing today and adding it back later costs a migration plus an unrecoverable backfill of rows whose currency nobody recorded.
- The expenses table also carries currency, snapshotted at write time, for the same reason.
- This is the one place this project deliberately builds something it does not yet need, and the reason is on the record.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
