# SW-ADR-041 — RLS covers every command, with WITH CHECK

> **⚠ SUPERSEDED 2026-08-05 by `SW-ADR-078`**, which corrects this record's premise
> about RLS write behaviour. `SW-ADR-071` additionally amends it on a narrower point
> (`password_resets` leaves RLS). Read `SW-ADR-078` first — `SW-ADR-132` corrects a
> banner that named only the incidental successor.

| Field | Value |
|---|---|
| ADR | `SW-ADR-041` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.2` · `SW-ADR-018` · `SW-ADR-009` |

## Context

SRC-001 §10.2 is phrased entirely about RETURNING rows, and the day-one gate proves exactly one thing: a denied READ. A FOR SELECT policy, or a FOR ALL policy with USING but no WITH CHECK, lets user B UPDATE or DELETE user A's expense by id, or insert a row already stamped with A's user_id — and every stated test still passes green.

## Options considered

- A. FOR ALL policies with both USING and WITH CHECK on every protected table.
- B. USING only, application layer for writes.

## Decision

**A. And the day-one proof is extended to include a denied WRITE and a denied DELETE, not only a denied read.**

## Consequences

- The gate as written cannot see this class of bug. This ADR changes the gate as well as the schema.
- Protected tables: expenses, categories, password_resets, sessions. See SW-ADR-042 for users and SW-ADR-043 for the admin path.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
