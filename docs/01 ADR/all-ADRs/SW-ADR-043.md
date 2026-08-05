# SW-ADR-043 — Admin database access: an explicit per-table policy matrix

| Field | Value |
|---|---|
| ADR | `SW-ADR-043` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §4.5` · `SRC-001 §7.6` · `SW-ADR-018` |

## Context

Every admin endpoint in SRC-001 §7.6 must cross the per-user boundary RLS enforces. The convenient fix — an admin escape hatch in the policy expression — would apply to EVERY table it is written on, including expenses, leaving SRC-001 §4.5 (admins never see amounts) enforced by application code alone. That is exactly the false green SW-ADR-018 exists to eliminate.

## Options considered

- A. An app.is_admin GUC consulted ONLY by the policies on sessions and password_resets, and deliberately NOT by those on expenses or categories, published as a table-by-table matrix.
- B. A third database role.
- C. Admin escape hatch on every policy.

## Decision

**A. And the matrix is published in the PRD as one table — one row per table, listing the user policy, the admin policy, and the commands covered.**

## Consequences

- C is the trap and is rejected explicitly: it would convert a database-enforced privacy rule into a code-review convention.
- The matrix exists so that 'did we consult the admin GUC here?' is answerable by reading one table rather than six policy definitions.
- CONSEQUENCE: admins CANNOT read expenses or categories at the database layer at all. SRC-001 §4.5 becomes structurally true rather than a rule someone must remember.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
