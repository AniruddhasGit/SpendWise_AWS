# SW-ADR-097 — `users` and `password_resets` sit outside RLS, with four compensating controls

| Field | Value |
|---|---|
| ADR | `SW-ADR-097` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-USERSRLS-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-USERSRLS-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-USERSRLS-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Option (a). Both tables are protected by the application layer. Four controls become MUSTs: (1) `password_hash` and `token_hash` never appear in any response model, and no repository method returns them outside the auth service; (2) reset tokens stay 32-byte urandom, SHA-256, unique, single-use; (3) the runtime role holds no ownership, no superuser, no BYPASSRLS, verified by the boot assertion including `SW-ADR-081`'s row_security check; (4) `FORCE ROW LEVEL SECURITY` stays on expenses, categories, sessions. The pre-auth-role option is recorded as the available stricter upgrade, not built in v1.

## Why

A GUC-keyed policy genuinely cannot serve a pre-authentication lookup, and `§10.5`'s timing defence needs that lookup to return empty rather than error — undisputed by the QA that withdrew the original. The product's central promise lives on expenses and categories, which keep full double enforcement; the stricter option buys marginal depth on two non-money tables at the cost of a third credential and a second pool on a 1 GB instance.

## Reversibility

yes — the pre-auth role is roles-and-wiring, addable any time with no schema change

> **⚠ FIRST IN THE CLIENT DIGEST.** This ruling formally crosses a line the register
> reserved. It is made under the client's escalation grant and is theirs to reverse.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-USERSRLS-01`, which is marked RULED in Article X with a pointer here.*
