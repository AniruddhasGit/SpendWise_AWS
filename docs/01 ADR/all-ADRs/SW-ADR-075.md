# SW-ADR-075 — The route map drops `/reset` — that question is the client's

| Field | Value |
|---|---|
| ADR | `SW-ADR-075` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-059` |
| Raised by | QA FINDING-9 (HIGH) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-059` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-059` put `/reset` in the route map. That silently closed `OPEN-RESETUI-01` — a `reserved: product` row — and answered it *differently* from the register's own recommendation. Article X's promise is that the build session raises open rows and may not close them.

## Decision

**`/reset` is struck from the route map. `OPEN-RESETUI-01` stays open. The remaining routes stand: `/`, `/signin`, `/admin`, `/admin/audit`, with period and category in the query string.**

## Consequences

- `SRC-001 §9.1` enumerates the pages and contains no reset page and no separate audit page. `/admin/audit` also needs the client's word or an erratum; raised as part of `OPEN-RESETUI-01`'s resolution.
- When the client rules, the route map is re-issued **together with** the three token-failure states the register says must accompany it — expired, already used, wrong.

---

*A superseding record, not an edit. `SW-ADR-059` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
