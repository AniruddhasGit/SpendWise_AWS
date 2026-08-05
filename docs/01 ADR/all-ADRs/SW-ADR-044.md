# SW-ADR-044 — Two database URLs, and a boot assertion that proves the runtime role is restricted

> **⚠ AMENDED 2026-08-05 by `SW-ADR-081` (QA FINDING-16 (MEDIUM)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-044` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §11.4` · `SRC-001 §11.6` · `SW-ADR-018` |

## Context

SW-ADR-018 mandates two roles; SRC-001 §11.4 names one DATABASE_URL and §11.6 runs migrations in the same container at start. The obvious build uses one URL for both, which makes the runtime connection the table owner — and a table owner can ALTER TABLE ... NO FORCE. The whole two-layer isolation decision then collapses silently, with no test going red.

## Options considered

- A. MIGRATION_DATABASE_URL and DATABASE_URL as separate variables, plus a startup catalog query asserting the runtime role owns no table and holds no BYPASSRLS.
- B. One URL.
- C. Migrations run by hand.

## Decision

**A. The assertion runs at boot and aborts startup on failure.**

## Consequences

- SW-ADR-018 already demanded catalog verification rather than assumption. This makes that verification a boot check rather than a one-time manual step, so it cannot rot.
- This is the single point where the isolation guarantee could collapse without anything turning red.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
