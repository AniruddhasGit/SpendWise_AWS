# SW-ADR-056 — Money is formatted with the en-IN grouping convention

| Field | Value |
|---|---|
| ADR | `SW-ADR-056` |
| Pack | `SPENDWISE_V1` |
| Type | UX_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §9.4` · `SW-ADR-013` |

## Context

SRC-001 §9.4 requires tabular figures so columns of money line up, and never states the digit-grouping convention. en-IN renders 1234567.89 as 12,34,567.89; en-US as 1,234,567.89. Same money, and an Indian user scanning the second reads the wrong magnitude.

## Options considered

- A. en-IN, through one shared formatter.
- B. en-US.
- C. No grouping.

## Decision

**A.**

## Consequences

- Follows SW-ADR-013's INR-only ruling to its display consequence.
- One shared formatter, so no component invents its own — which also makes the formatting assertable in a test.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
