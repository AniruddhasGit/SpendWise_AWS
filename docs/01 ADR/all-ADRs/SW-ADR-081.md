# SW-ADR-081 — Migrations must be able to touch rows in RLS-protected tables

| Field | Value |
|---|---|
| ADR | `SW-ADR-081` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-044` |
| Raised by | QA FINDING-16 (MEDIUM) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-044` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`FORCE ROW LEVEL SECURITY` subjects the table **owner** to the policies, and `SW-ADR-044` makes the owner the migration role. So any data migration — a backfill, or `SRC-001` erratum E-7's currency column on existing rows — runs with the user-id GUC unset and either errors or **silently affects zero rows**. The silent branch is the dangerous one: the migration reports success, the chain advances, the data is untouched.

## Decision

**`env.py` issues `SET LOCAL row_security = off` on the migration connection. The migration role may do this because it owns the tables; the runtime role cannot, because it lacks `BYPASSRLS` — so the isolation guarantee is untouched.**

## Consequences

- `SW-ADR-044`'s boot assertion is extended: it must also confirm the RUNTIME role cannot turn row security off. Proving the migration role can is not enough.
- This is precisely the class of collapse `SW-ADR-044` warned 'could happen without anything turning red' — and it was reachable through the ADR's own design.

---

*A superseding record, not an edit. `SW-ADR-044` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
