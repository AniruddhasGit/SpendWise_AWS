# SW-ADR-103 — Password policy

| Field | Value |
|---|---|
| ADR | `SW-ADR-103` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-PWPOLICY-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-PWPOLICY-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-PWPOLICY-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Minimum **12 characters**; maximum **72 bytes** measured after UTF-8 encoding; no composition rules; no common-password list in v1. Enforced in the Pydantic schema at registration and reset-completion. The 72 is documented as a bcrypt property — a hard input bound, never to be raised, so nobody 'improves' it into silent truncation.

## Why

Length over composition matches current guidance and closes both stated defects: the one-character password, and two long passphrases sharing a 72-byte prefix authenticating each other.

## Reversibility

yes — validator constants; existing hashes unaffected

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-PWPOLICY-01`, which is marked RULED in Article X with a pointer here.*
