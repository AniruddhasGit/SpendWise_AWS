# SW-ADR-107 — User deletion does not exist in v1

> **⚠ SUPERSEDED 2026-08-06 by `SW-ADR-150`**, on the exact terms this record named:
> *"When deletion comes, it arrives as a client-run runbook plus a superseding ADR."*
> `CR-001` is the client's instruction and `SW-ADR-150` is the record. Deletion is **soft** —
> a `deleted_at` timestamp, every row retained, restorable by an administrator — so the
> one-way door this ruling was guarding is still shut. Read `SW-ADR-150` for what a person
> can now do; the reasoning below is why it took an authority above the build session to
> allow it.

| Field | Value |
|---|---|
| ADR | `SW-ADR-107` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-USERDEL-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-USERDEL-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-USERDEL-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

No endpoint, no screen, no admin power, no seed-script back door. The `§6.9` cascade semantics stay in the schema as correctness — `ON DELETE CASCADE` on categories/expenses/sessions, no FK from the audit log — so a future deliberate deletion behaves exactly as the client specified. When deletion comes, it arrives as a client-run runbook plus a superseding ADR.

## Why

`§4.2`'s matrix grants the permission to no one and `§7.6` exposes no endpoint — the capability was implied by prose, never granted. Deleting a person's financial history is the clearest one-way door in the register.

## Reversibility

yes as ruled; the avoided action is the irreversible one

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-USERDEL-01`, which is marked RULED in Article X with a pointer here.*
