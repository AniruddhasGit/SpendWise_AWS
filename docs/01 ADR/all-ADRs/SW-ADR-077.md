# SW-ADR-077 — Admin expense counts: a COUNT-only policy

> **⚠ AMENDED 2026-08-05 by `SW-ADR-129`.** The decision below is **not
> implementable as specified** — a row-level policy has no column dimension, so
> "aggregate reads only" cannot be expressed as one. Replaced by a
> `SECURITY DEFINER` function whose *return type* is the guard.

| Field | Value |
|---|---|
| ADR | `SW-ADR-077` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-030` |
| Raised by | QA FINDING-11 (HIGH) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-030` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-030` says every admin read is a service call, citing `SRC-001 §3.4`'s own worked example — "if `admin` needs expense counts, it calls the expenses service". `SW-ADR-043` says admins cannot read expenses at the database layer at all. The service call runs on the runtime role under a policy keyed on the admin's own user id, so it returns zero. `SW-ADR-030`'s architecture was unimplementable.

## Decision

**The `expenses` table gains one additional policy, consulted only when `app.is_admin` is set, permitting **aggregate reads only** — the expenses service exposes a single admin-facing method returning a count and a last-activity timestamp, through a response model with no field capable of holding an amount or a description.**

## Consequences

- `SRC-001 §4.5` stays structurally true: the response type physically cannot carry a forbidden value, so the rule is enforced by the type checker rather than by memory.
- `SW-ADR-043`'s per-table policy matrix must be updated to show this asymmetry explicitly — it is the one place an admin GUC touches a money table, and the reason it is safe is the response shape, not the policy.
- `SRC-001 §7.6`/`§9.3` do not currently name an expense-count endpoint, so this is latent until the PRD writes the admin screen. It is ruled now precisely so it is not discovered then.

---

*A superseding record, not an edit. `SW-ADR-030` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
