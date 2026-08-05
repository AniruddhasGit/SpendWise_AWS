# SW-ADR-130 — A forged owner id in a create body is ignored, and the create succeeds

| Field | Value |
|---|---|
| ADR | `SW-ADR-130` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice, GUESS #5 (BLOCKING) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.2` · `P-REC-01` · negative case `NEG-X-10` · the GOAL_13 uncoached vertical slice, 2026-08-05 |

## Context

Two documents a builder must both satisfy disagreed. `P-REC-01`: *"a forged owner id, a forged total or a forged record id in the request body is **ignored**"* — the row is created, under the caller's own identity. Bible `E0-S6` and `SIT-E0-S6-03` agree: *"has no effect on the stored row."* But negative case `NEG-X-10`, severity one, expects **404** for `POST /api/expenses {user_id: A}`.

They cannot both pass. The negative suite's cross-person block shares one templated `expected_status` across all sixteen cases — which is how a *read* expectation ended up on a *create*.

## Decision

****201, with the forged field ignored.** A create carries no target: the owner is taken from the verified identity and any `user_id`, `id`, or server-derived total in the body is discarded before validation. There is nothing to be denied access *to*, so 404 is the wrong shape.

`NEG-X-10` is corrected: expected status **201**, and the assertion becomes *the stored row carries the caller's user_id, not the forged one* — which is the property that actually matters and which a 404 would not have proved.**

## Consequences

- **404 remains correct for every case that names an existing row** — read, update, delete. Those have a target; a create does not.
- The row-level `WITH CHECK` clause is the backstop: even if the application forgot to discard the field, the database refuses an insert stamped with another identity (`NEG-X-18` proves this, at the database, as the runtime role).
- **A templated expectation is still an expectation on file.** This one was templated across sixteen cases and was wrong on two of them; both are now stated individually.

---

*A superseding record, not an edit. The superseded text stays in place with a banner
pointing here — Art III.2.*
