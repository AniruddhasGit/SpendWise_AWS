# SW-ADR-098 — Admin-on-admin: guard extended, peer reset refused

> **⚠ AMENDED 2026-08-06 by `SW-ADR-148`.**
> The ruling below stands in full and is implemented. What changed is the *premise* of
> Decision (4): it reasons "with no self-service password change, that is the only
> password-change route anyone has", and `SW-ADR-148 D` added one. The sentence is now
> historical; the ruling is not.

| Field | Value |
|---|---|
| ADR | `SW-ADR-098` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-ADMINSELF-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-ADMINSELF-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-ADMINSELF-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

(1) The last-admin guard extends from demotion to **every** action that would leave zero active admins — any demote or deactivate, self or other, refused with 409. (2) Admin-on-admin promote/demote/deactivate allowed subject to that guard. (3) **Admin-on-admin password reset is refused (403)** — to reset a peer, demote them first, then reset: two deliberate, separately audited steps instead of a one-click takeover. (4) An admin MAY reset themselves — with no self-service password change, that is the only password-change route anyone has. (5) Force sign-out against another admin is allowed; it is containment and fully reversible by signing back in.

## Why

`§4.4` guards only self-demotion while the identical lockout is reachable through deactivate, and recovery would be hand-written SQL. The register's real reservation is peer takeover; demote-then-reset removes the silent single act while keeping every capability the matrix grants.

## Reversibility

yes — request-handler rules. The state they prevent (zero admins) is the irreversible thing.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-ADMINSELF-01`, which is marked RULED in Article X with a pointer here.*
