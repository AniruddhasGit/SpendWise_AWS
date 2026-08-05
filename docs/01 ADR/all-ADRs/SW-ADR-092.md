# SW-ADR-092 — The eight seeded categories and their colours

| Field | Value |
|---|---|
| ADR | `SW-ADR-092` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-CAT-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-CAT-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-CAT-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Groceries `#4a7c59` · Food & Dining `#b5543b` · Transport `#3e6b8f` · Rent & Utilities `#9c7a2f` · Health `#2e7d8a` · Entertainment `#7b4b94` · Shopping `#a04c72` · Other `#7d8471`. In that order. The day-one fixture uses exactly this list. The design system adopts them as tokens and MUST verify each at >=3:1 against the paper surface, adjusting tone within hue if any fails.

## Why

Content, but not money, legal posture or identity — and the client's instruction was to pick a correct generic answer rather than stall. These are the standard buckets of Indian personal spending, on a palette anchored to the client's own paper-and-pine-green identity with hue spacing wide enough for the ribbon.

## Reversibility

partly — the list changes for new accounts in one message with zero migration; existing accounts keep theirs and can rename/recolour

> **⚠ IN THE CLIENT DIGEST.** Ruled under the escalation grant; one message reverses it.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-CAT-01`, which is marked RULED in Article X with a pointer here.*
