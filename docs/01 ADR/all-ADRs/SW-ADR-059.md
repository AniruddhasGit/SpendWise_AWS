# SW-ADR-059 — The route map, with period and filter in the query string

> **⚠ AMENDED 2026-08-05 by `SW-ADR-075` (QA FINDING-9 (HIGH)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-059` |
| Pack | `SPENDWISE_V1` |
| Type | UX_CONTRACT |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §9.1` · `SRC-001 §9.2` · `SW-ADR-020` |

## Context

No route is named anywhere. SRC-001 §9.2 makes the ribbon THE filter control, so filtered views are a primary state — yet refreshing after clicking a band would silently drop both the filter and the period, and the user would believe their data changed.

## Options considered

- A. `/` dashboard with from/to/category in the query string; `/signin`; `/reset`; `/admin`; `/admin/audit`. Panel state is not in the URL.
- B. Component state only.
- C. localStorage.

## Decision

**A.**

## Consequences

- Refresh, back-button and deep-linking all become correct for free.
- Unmatched /api/* paths return a JSON 404 rather than falling through to SW-ADR-020's SPA catch-all — otherwise a typo'd API path returns HTML with a 200 to a caller expecting JSON.
- A non-admin reaching /admin gets an explicit no-access screen, not the admin shell failing request by request.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
