# SW-ADR-007 — Requirements arrive as an unstructured dump, then are interrogated

| Field | Value |
|---|---|
| ADR | `SW-ADR-007` |
| Pack | `SPENDWISE_V1` |
| Type | PROCESS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-002 §1` · `SRC-002 §8` |

## Context

The client's normal working pattern is a meeting, then minutes, then handing the minutes to a model. That shape had to be either adopted or replaced with an interview.

## Options considered

- A. Dump, then interrogate the gaps.
- B. Interview question by question.
- C. Dump only; the build session fills gaps itself.

## Decision

**A. The client writes requirements out however they come; the build session converts them to cited rows and returns with everything the dump did not settle.**

## Consequences

- Executed 2026-08-05: the dump was filed as SRC-001 and produced five contradictions, seven gaps and three factual errors, all raised BEFORE any specification was written.
- STANDING RULE attached to this ruling: nothing the dump leaves open is filled with something plausible. It becomes an OPEN row. This is the rule under most pressure in a single-person project, because the person who could answer is always right there and assuming is always faster.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
