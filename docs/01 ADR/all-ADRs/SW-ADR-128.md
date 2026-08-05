# SW-ADR-128 — The rate-limit numbers

| Field | Value |
|---|---|
| ADR | `SW-ADR-128` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-RATE-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-RATE-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-RATE-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Dual-keyed, stated as **effective** limits with per-worker configuration at half (2 uvicorn workers, 1 task; slowapi is per-process): **Login** 10/min per IP and 10/min per normalized email (configured 5+5). **Reset completion** 6/min per IP (configured 3). **Registration** 5/min and 20/day per IP (configured 3/min, 10/day). **Everything else** 120/min per authenticated user id, 60/min per IP for unauthenticated API paths (configured 60 and 30). Static assets unlimited. 429 uses the standard error envelope plus a `Retry-After` header. The IP key comes from the socket-unless-trusted-proxy resolution. All numbers live in settings and `.env.example`. **Accepted and restated knowingly:** the in-process store resets on every restart and multiplies by task count if the client ever scales out — recorded, not fixed.

## Why

`§10.9` cannot ship as prose — without numbers no acceptance criterion here is binary. Halving the configured value is what makes the effective limit the stated one on this exact topology, and dual keying stops one NAT-load of users being locked out by one attacker, or one account being hammered from many IPs.

## Reversibility

yes — env-tunable constants

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-RATE-01`, which is marked RULED in Article X with a pointer here.*
