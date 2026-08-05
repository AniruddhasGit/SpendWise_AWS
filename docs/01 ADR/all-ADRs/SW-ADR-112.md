# SW-ADR-112 — More than two decimal places is rejected, never rounded

| Field | Value |
|---|---|
| ADR | `SW-ADR-112` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-DECIMALS-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-DECIMALS-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-DECIMALS-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

422 — 'Amount must have at most two decimal places.' **No rounding on the write path.** The React amount input restricts entry to two decimals with live validation, so the 422 is a backstop a user should never meet.

## Why

A rounded third digit is stored nowhere, so rounding silently destroys what the user typed with no path back. `SRC-002 §14`'s 'till .00 then round it off' reads as the display convention `SW-ADR-013` already implements, not a write-path mandate.

## Reversibility

yes — a validator change. Past rejections cost nothing; past roundings would have been unrecoverable.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-DECIMALS-01`, which is marked RULED in Article X with a pointer here.*
