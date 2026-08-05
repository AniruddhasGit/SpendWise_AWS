# SW-ADR-140 — The route inventory is data, and every route a test names must resolve

| Field | Value |
|---|---|
| ADR | `SW-ADR-140` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice run 3 — contradiction C2 and PART 4 |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-138` · `SW-ADR-050` · Bible `E0-S7` · `NEG-X-01` |

## Context

**`GET /api/expenses/{expense_id}` did not exist in any contract document.**

It is required by Bible `E0-S7 AC1` — *"as B, `GET /api/expenses/{A's id}` returns 404"* — by
`SIT-E0-S7-01`, and by `NEG-X-01`, a **severity-one** cross-person case. `CV-11`'s whole ruling
about route declaration order only bites if a `GET` exists on that path.

`PRD §6` listed `PATCH·DELETE` on `/api/expenses/{id}` and no `GET`. `05_surface_route_map.md`
listed the same. `CROSS_PERSON_COVERAGE.tsv` — written at this same exit gate, three hours earlier
— listed PATCH and DELETE, **omitted `NEG-X-01` entirely, and declared every route COVERED.**

Three hand-maintained copies of one table, all missing the same row, one of them a coverage matrix
whose entire purpose was to prove nothing was missing. This is precisely the failure `SW-ADR-138`
diagnosed for payloads, in the artifact next door, committed by the same session on the same day.

## Decision

**The route inventory lives in `docs/03 PRD/api/contract.json` under `routes`, as data.** Each
row carries method, path, who may call it, the `P-` specifications it implements, its request and
response models, and **the closed set of error codes it may return**. `PRD §6`'s table is
generated from it between markers.

**`consistency_check.py` gains a `route-contract` gate.** It parses every `METHOD /api/…` string
out of the Bible, `08 SIT`, `09 NegativeTesting` and `11 Journeys`, normalises the path
placeholder, and **fails** if one does not resolve to a declared route. On the day it was written
it checked 78 named routes against 28 declared.

`GET /api/expenses/{expense_id}` is added, with `P-REC-02` and `P-PRV-03` as its specifications
and `NOT_FOUND` in its error set.

## Consequences

- **A test may now name a route the contract does not have, exactly once** — the next run of the
  checker fails. That is the direction that matters: the tests are downstream of the contract, and
  the tests were right.
- The placeholder name is normalised, so `{id}`, `{expense_id}` and `{A's id}` are one route. A
  checker that treated them as three would have produced noise instead of this finding.
- `05_surface_route_map.md`'s "Verified 2026-08-05: 25 PRD routes, all covered" was verifying the
  wrong set. The count is now generated.
- **The pattern is now uniform across the project**: `datamodel.json` for the schema,
  `contract.json` for the API. Both have a `--check` that regenerates and compares content, and
  `consistency_check.py` runs both.

---

*Ruled under `SW-ADR-015`. It supersedes nothing.*
