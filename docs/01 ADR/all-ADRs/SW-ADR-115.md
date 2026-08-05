# SW-ADR-115 — Description is optional, 500 characters, normalized

| Field | Value |
|---|---|
| ADR | `SW-ADR-115` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-DESC-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-DESC-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-DESC-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Optional. Maximum 500 characters. Empty or whitespace-only strings are **normalized to NULL** so 'no description' has exactly one representation.

## Why

The normalization closes the ''-versus-NULL dual state before any data exists.

## Reversibility

yes

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-DESC-01`, which is marked RULED in Article X with a pointer here.*
