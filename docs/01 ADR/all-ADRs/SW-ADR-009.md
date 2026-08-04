# SW-ADR-009 — Clean-clone evidence without a pipeline: a labelled substitute ladder

| Field | Value |
|---|---|
| ADR | `SW-ADR-009` |
| Pack | `SPENDWISE_V1` |
| Type | QUALITY_GATE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §10` · `SRC-001 E-6` |

## Context

The day-one proof requires that everything ran on a clean clone, not only on the developer's machine. The purpose is not CI worship - it is proving no setup step is hiding in one machine's accumulated state. With CI owned by the client's separate DevOps work, that evidence has to come from somewhere else.

## Options considered

- A. A clean-container run now; the client closes the real CI tick later.
- B. Leave the item formally OPEN until CI exists.
- C. Treat a container run as fully satisfying it and never reopen.

## Decision

**A. A labelled substitute now, with the original left explicitly OPEN.**

## Consequences

- The evidence record carries FOUR lines, never one:
-   J1-SUBSTITUTE-A  fresh clone into an empty directory + a brand-new virtualenv + the database dropped and rebuilt from empty
-   J1-SUBSTITUTE-B  clean-container run - OPEN, needs the Dockerfile that SW-ADR-011 defers
-   J1  ran in CI - OPEN, the client's DevOps work
-   J2  ran on a hosted runner - OPEN, the client's DevOps work
- Substitute A proves no PROJECT state is hiding on this machine. It does NOT prove the host toolchain is reproducible. That hole is written down, not papered over.
- A check may be substituted in the open. It may not be quietly redefined.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
