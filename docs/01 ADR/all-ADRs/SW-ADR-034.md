# SW-ADR-034 — Category colour is stored as a 7-character lowercase hex string

| Field | Value |
|---|---|
| ADR | `SW-ADR-034` |
| Pack | `SPENDWISE_V1` |
| Type | DATA_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.5` · `SRC-001 §9.4` |

## Context

SRC-001 §6.5 says 'color hex' and stops.

## Options considered

- A. CHAR(7) matching ^#[0-9a-f]{6}$, enforced by CHECK and Pydantic.
- B. Store without the leading hash.
- C. Accept 3-digit shorthand and expand.

## Decision

**A. Exactly `#rrggbb`, lowercase, validated at both layers.**

## Consequences

- One canonical form means React never has to normalise before rendering, and two rows cannot differ only by case or shorthand.
- The eight seeded colours must come from the design system of GOAL_04, not be invented here — see OPEN-CAT-01.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
