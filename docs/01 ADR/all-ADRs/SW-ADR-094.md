# SW-ADR-094 — Where credentials live

| Field | Value |
|---|---|
| ADR | `SW-ADR-094` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-CREDS-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-CREDS-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-CREDS-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Local: git-ignored `.env`, with `.env.example` as the manifest. AWS: SSM Parameter Store, both `DATABASE_URL` and `JWT_SECRET` as **SecureString**. The role-creation SQL is run by the client by hand via psql; the build session supplies the file and never receives, requests or handles a live credential in chat or in any committed file.

## Why

The only arrangement in which no credential ever crosses the build session's boundary, which keeps `SW-ADR-005`'s code-only bargain and Art III.4 trivially true.

## Reversibility

yes — a secrets location changes by rotating into the new home

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-CREDS-01`, which is marked RULED in Article X with a pointer here.*
