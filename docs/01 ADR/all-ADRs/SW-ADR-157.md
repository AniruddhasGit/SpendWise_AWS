# SW-ADR-157 — Amounts are shown in US dollars

| Field | Value |
|---|---|
| ADR | `SW-ADR-157` |
| Pack | `SPENDWISE_V1` |
| Type | UX_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instruction 2026-10-20 ("replace rupees to dollars from everything") |
| Decision date | 2026-10-20 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Supersedes | `SW-ADR-056` (en-IN grouping) |
| Amends | `SW-ADR-013` (display currency only; storage unchanged, see below) |
| Sources | owner instruction 2026-10-20 · `SW-ADR-013` · `SW-ADR-056` · `SW-ADR-156` |

## Context

Every amount on screen was rupees: a `₹` sign, lakh and crore grouping (`₹12,34,567.89`), "Know
where every rupee goes." on the landing page, and the money tree's example bills (Chai, Auto,
Biryani). The owner asked for dollars everywhere.

## Decision

1. **Display.** The one money formatter (`client/src/lib/money.js`, now `dollars()`) writes `$` and
   groups by thousands (`en-US`): `$1,234,567.89`. Two decimals, as before. The chart's compact tick
   labels read `k`, `M`, `B` instead of `k`, `L`, `Cr`. The amount field's sign, the landing and
   sign-in headline ("Know where every dollar goes.") and the tree's example bills (Pizza $10,
   Coffee $4.50, ...) follow.
2. **Arithmetic is untouched.** Amounts are still integers in hundredths of the unit, so every
   figure is the same integer it was: the day-one gate is still exactly `75810`, now shown as
   `$758.10`.
3. **Names on the wire are untouched.** The integer fields stay `*_paise` in the API contract, the
   models and the database. They now hold cents. Renaming a contract field is a breaking API change
   and is not what was asked.

## Not done, and why (`SW-ADR-015`: reserved and irreversible waits for the client)

- **The stored currency code is still `INR`.** `SW-ADR-013` (CLIENT) snapshots a currency code onto
  every user and every expense, enforced by `CHECK (currency = 'INR')`, and the API returns it.
  Changing it means a migration that rewrites every row in the live database, which is exactly the
  silent reinterpretation `SW-ADR-013` exists to prevent. No screen shows the code. It changes with
  one message from the owner: a migration to `USD` (drop the checks, update the rows, re-add the
  checks), the data model package regenerated, and the three test assertions that read `INR`.
- **The showcase data keeps its numbers.** The seeded demo accounts were written at Indian prices,
  so a rent of 18,000 now reads `$18,000.00`. Rescaling them is a data change on the live database
  and was not asked for.

## Tests

- Browser assertions that read a formatted figure now expect `$` (`$3,790.49`, `$758.10`,
  `$1,250.00`, `$0.00`). Same figures, same strictness; the symbol is the specified display. No
  assertion was removed or loosened. The admin console checks now assert no `$` reaches it.
- `test_the_money_is_formatted_en_in` is renamed `..._en_us`; it asserts the same element.

## Consequences

- `SW-ADR-056` is superseded. `SW-ADR-013` stands for storage and is amended for display.
