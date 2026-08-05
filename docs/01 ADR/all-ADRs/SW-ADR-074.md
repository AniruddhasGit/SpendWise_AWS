# SW-ADR-074 — Receipts: ownership, not role

| Field | Value |
|---|---|
| ADR | `SW-ADR-074` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-046` |
| Raised by | QA FINDING-8 (HIGH) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-046` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-046` said receipts endpoints "reject the admin role outright". `SRC-001 §4.2` grants admin **yes** on "Own expenses and categories" — an admin is also a user with their own expenses. The ruling removed a capability the frozen source grants, which is a scope reduction reserved to the client, and its wording was ambiguous on a security control: "reject the admin role" could mean two different things and two implementers would build both.

## Decision

**Receipts endpoints resolve the key **only** from an expense row owned by the caller. There is no admin escape path and no role check at all — ownership is the whole rule.**

## Consequences

- Achieves `SRC-001 §4.5` exactly (an admin can never reach another user's receipt) while leaving `§4.2` intact (an admin keeps their own).
- A rule expressed as ownership rather than as a role cannot be misread, and does not need revisiting if a third role ever appears.
- `SW-ADR-046`'s key-derivation half stands unchanged: the server derives every key from the verified user id and never accepts one from the client.

---

*A superseding record, not an edit. `SW-ADR-046` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
