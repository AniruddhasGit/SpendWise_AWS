# SW-ADR-093 — Migrations run at container start — `SW-ADR-019` wins

| Field | Value |
|---|---|
| ADR | `SW-ADR-093` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-MIGRATE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-MIGRATE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-MIGRATE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

`SW-ADR-019` governs. Migrations run at container start, before uvicorn binds the port, wrapped in an explicit `pg_advisory_xact_lock`, with `SW-ADR-061`'s timeouts and no-retry-exit-nonzero. `SW-ADR-005`'s consequence line 'migrations a separate runnable step, never done on boot' is superseded **on that one point only**; every other clause of `SW-ADR-005` stands.

## Why

Art II.1 puts raw `SRC-001` above any ADR, and `SRC-001 §11.6` — the client's own hand — says 'at container start, before uvicorn binds the port'. Erratum E-4 corrected only the false advisory-lock premise. The losing sentence is a drafter's gloss inside a decision about *who writes what*, not about migration timing. It is also the worse answer here: the client deploys by hand with no pipeline, so a separate step is one a human must remember every time, and a forgotten one is new code against an old schema.

## Reversibility

yes — moving migrations out of boot later is operational only

> **⚠ IN THE CLIENT DIGEST.** Ruled under the escalation grant; one message reverses it.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-MIGRATE-01`, which is marked RULED in Article X with a pointer here.*
