# SW-ADR-095 — What may enter a model

| Field | Value |
|---|---|
| ADR | `SW-ADR-095` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | DEFAULT_TO_PROCEED_CLIENT_RETAINS |
| Closes | `OPEN-MODEL-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-MODEL-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-MODEL-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Default to proceed: repository code, documents and synthetic fixtures MAY enter models — they are already model-authored and hold no personal data. **No real user data ever** — production database contents, real emails, password material, real receipt images. Revisit before any real third-party user exists. SpendWise has zero real users today, so nothing is blocked.

## Why

The line that matters is repo-content versus user-content, and the conservative version costs nothing now. The sub-processor question becomes real only when real user data exists — a moment the client controls.

## Reversibility

yes for the default; the legal posture stays open

> **⚠ NOT RULED — CLIENT ONLY.** Fable 5 declined: this is not a question any model may
> answer. What is recorded here is the **default to proceed on**, so nothing blocks.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-MODEL-01`, which is marked RULED in Article X with a pointer here.*
