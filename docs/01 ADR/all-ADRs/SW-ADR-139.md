# SW-ADR-139 — Eleven API conventions that were never written down

| Field | Value |
|---|---|
| ADR | `SW-ADR-139` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice runs 1 and 2 |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-138` · the two uncoached vertical slices, 2026-08-05 |

## Context

Two engineers read this document set cold, three hours apart, and were asked to plan the same
vertical slice. Neither could ask a question. Between them they logged **thirty-nine** things they
had to invent.

Most were the same eleven conventions, and they are the kind nobody writes down because everybody
assumes they are obvious: what the session cookie is called, whether `"1250.0000"` is four decimal
places or two, whether a `201` carries a `Location` header, which route has to be declared first.

Neither reader was confused about *behaviour* — the PRD specifies behaviour well. They were
stuck on **surface**, and every one of them chose a defensible answer that a second engineer
could equally defensibly have chosen differently.

## Decision

**All eleven are ruled in `docs/03 PRD/api/contract.json` under `conventions`, and rendered into
PRD §6.2 by `generate_api.py`.** `CV-01`…`CV-11`, each with the question as asked, the ruling, the
reason, its source, and **which slice raised it**.

Two are worth restating here because a wrong choice is silent rather than loud:

- **`CV-06` — the clock.** "Today" is mocked through a FastAPI dependency, **not** a library that
  freezes the process clock. Freezing the process clock does not freeze `now()` inside PostgreSQL,
  so session expiry and `spent_on` validation would disagree about what day it is, intermittently,
  near midnight.
- **`CV-11` — route order.** `/api/expenses/summary` must be declared **before**
  `/api/expenses/{expense_id}`. Declared the other way the literal `summary` is captured by the
  integer path parameter and the endpoint returns 422 — the day-one gate would fail with a
  validation error against a route that exists.

## Consequences

- **The table keeps the "raised by" column.** It is a record of where the document set was thin,
  not only of what it now says — and the pattern in that column (surface, not behaviour) is more
  useful than any individual row.
- **§6.2 closes the list.** A convention absent from §6.1 and §6.2 is not a licence to choose one;
  it is an `OPEN` item, and Art X applies: escalate, never invent.
- The rulings are conventions, not behaviour, so none is reserved. Each is one line to reverse.

---

*Ruled under `SW-ADR-015`. It supersedes nothing.*
