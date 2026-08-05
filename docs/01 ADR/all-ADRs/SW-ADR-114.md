# SW-ADR-114 — Categories can be renamed and recoloured

| Field | Value |
|---|---|
| ADR | `SW-ADR-114` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-RENAME-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-RENAME-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-RENAME-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

An update endpoint on categories accepting `name` and/or `color`. Renaming never touches expenses — `category_id` links are untouched, history follows the category. Name conflicts return 409 under the per-user case-insensitive uniqueness rule.

## Why

`§7.2`'s own justification — 'I don't want to lose history because I renamed something' — assumes the capability its endpoint list omits. The prose is the intent; the list is the accident. Recolour rides along free and makes the seeded palette fully soft for existing accounts.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-RENAME-01`, which is marked RULED in Article X with a pointer here.*
