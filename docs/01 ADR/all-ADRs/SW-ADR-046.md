# SW-ADR-046 — Receipt keys are derived server-side; the admin role cannot reach receipts

> **⚠ AMENDED 2026-08-05 by `SW-ADR-074` (QA FINDING-8 (HIGH)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-046` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §8.3` · `SRC-001 §7.5` · `SRC-001 §4.5` |

## Context

SRC-001 §8.3's prefix guarantee is scoped to the ATTACH verb only. If the upload-URL endpoint signs a caller-supplied key, user B obtains a PUT capability for user A's prefix. If the view-URL endpoint signs whatever key it is handed, possession of a key is sufficient to read the image. And a receipt image carries amounts and descriptions in the most literal form possible.

## Options considered

- A. The server derives every key from the verified user id and never accepts one from the client; view and delete resolve the key from the owned expense row. Receipts endpoints reject the admin role outright.
- B. Apply the §8.3 prefix check on all four verbs.

## Decision

**A.**

## Consequences

- SRC-001 §4.5 has no support-reason exception, and a receipt is the densest possible carrier of the forbidden data — so an admin reaching a receipt is the cleanest breach of the privacy rule available in this system.
- B was rejected as the sole control: four places to remember is four places to forget one.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
