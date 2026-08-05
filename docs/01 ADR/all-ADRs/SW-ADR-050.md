# SW-ADR-050 — A uniform 404 for every not-yours-or-not-found case

| Field | Value |
|---|---|
| ADR | `SW-ADR-050` |
| Pack | `SPENDWISE_V1` |
| Type | API_CONTRACT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.2` · `SW-ADR-023` · `SW-ADR-041` |

## Context

A 403 on someone else's expense and a 404 on a nonexistent one is a working oracle: walk the id space, learn which ids are real and how fast other people are spending. Worse on the write verbs, where DELETE returning 403 versus 404 distinguishes the two cases even when the read path was careful.

## Options considered

- A. 404 for every not-yours-or-not-found case, on every verb, reads and writes alike.
- B. 403 when the row exists.
- C. Different rules per router.

## Decision

**A. Stated once as a global convention rather than per endpoint.**

## Consequences

- Under SW-ADR-041's RLS design the two cases are already indistinguishable at the database layer — a filtered query returns zero rows for both — so the leak could only be introduced by the application deliberately telling them apart.
- This ADR is what makes SW-ADR-023's sequential integer ids safe. The two must be reversed together or not at all.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
