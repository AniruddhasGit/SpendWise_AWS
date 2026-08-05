# SW-ADR-134 — Cross-person coverage is extended to every route; E6-S3's wording is untouchable

| Field | Value |
|---|---|
| ADR | `SW-ADR-134` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 exit gate, X-01 FINDING-16 |
| Decided by | **FABLE_5** (escalation tier, under the client's standing instruction) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | Art IX.2 · Art IX.6 · `ISOLATION_ATTACK_PLAN.md` · `SW-ADR-130` · Fable 5 adjudication, 2026-08-05 |

## Context

Bible `E6-S3` carries a P0 binary acceptance criterion: *"every endpoint has at least one
cross-person case"*. The suite reached roughly nine of the 25 API routes, so the criterion could
not pass. The tempting fix was to narrow it to "every endpoint that **returns person-owned
data**".

## Decision

**Add the coverage. `E6-S3`'s text does not change, and the build session may not change it.**

The criterion is not over-broad. "Cross-person case" is defined by `E6-S3`'s own cited source —
`ISOLATION_ATTACK_PLAN.md`, whose brief is goal-based (*make person B observe **any** data
belonging to person A*) and whose surfaces explicitly include the admin surface in both
directions. Under that definition a coherent cross-person case exists for **every** route.

Narrowing was denied on three independent grounds:

1. It narrows a **P0 criterion specifically to turn a red check green without work** — the
   definitional Art IX.2 violation. Redefining "done" is reserved, and the client is unavailable.
2. It is **unnecessary**: a strictly stronger compliant path exists, and Art IX.6 says the
   stricter option needs no signature.
3. **The proposed wording fails on its own terms.** "Returns person-owned data" still captures
   `/api/auth/me`, `/api/admin/users` and `/api/admin/sessions` — emails, names and activity
   times are person-owned — while excluding `POST /api/auth/reset/complete`, the
   account-takeover surface, which is the last endpoint an isolation suite should ever exclude.

**Seven cases are added** (`NEG-X-23`…`NEG-X-29`), and a **25-route coverage matrix** is published
beside the attack plan, citing the `NEG-R`/`NEG-T`/`NEG-A`/`NEG-I` rows where coverage already
arrives under a different class label. Every row non-empty makes the criterion auditable and green
**as written**.

`NEG-X-24`'s expectation is shaped per `SW-ADR-130` — a forged owner on a create is **ignored,
201**, not 404 — rather than copying the by-id template that caused that defect.

## Consequences

- Much of the "missing" coverage already existed under other labels: `NEG-R-01`…`07` hit every
  admin endpoint as a non-admin person, `NEG-R-08` forbids a monetary value in any `/api/admin/*`
  response, `NEG-T-01`…`05` are reset-token takeover, `NEG-A-09` is a crafted `jti`. The matrix
  makes that visible instead of leaving it to be rediscovered.
- The highest-value genuine hole was **list isolation on `/api/categories`**: the expenses list
  had four cross-person cases and the categories list had none.
- On the record: standalone narrowing would have been **RESERVED** — the build session must stop
  if anyone attempts it.

---

*Ruled at the Fable 5 escalation tier. Purely additive; it supersedes nothing.*
