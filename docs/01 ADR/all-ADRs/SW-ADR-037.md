# SW-ADR-037 — One receipt per expense

> **⚠ AMENDED 2026-08-05 by `SW-ADR-087` (QA FINDING-24 (LOW)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-037` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT_RULE |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §6.6` · `SRC-001 §7.5` |

## Context

SRC-001 §6.6 gives expenses a single nullable `receipt_key`, which implies one receipt, but §7.5's endpoint list never says so.

## Options considered

- A. Exactly one; attaching a second replaces the first.
- B. Many, via a child table.

## Decision

**A. One. Attaching replaces, and the replaced object is deleted from S3 in the same operation.**

## Consequences

- Follows the column shape SRC-001 §6.6 already chose rather than inventing a table it does not describe.
- The replaced-object deletion closes one of the four S3 orphan paths; the rest are OPEN-S3LIFE-01.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
