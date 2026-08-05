# SW-ADR-145 — `limit` is clamped, `offset` is refused, and the difference is the registry

| Field | Value |
|---|---|
| ADR | `SW-ADR-145` |
| Pack | `SPENDWISE_V1` |
| Type | CLARIFICATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | — |
| Raised by | GOAL_14 M2 implementation (`GET /api/expenses`) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-144 B` · `P-REC-02` · `SW-ADR-038` · `NEG-X-12` · `error_codes.messages.rules` |

## Context

`ExpenseListQuery` gives `limit` and `offset` symmetric-looking notes:

| field | default | note |
|---|---|---|
| `limit` | 50 | *maximum 200* |
| `offset` | 0 | *`NEG-X-12` requires "422 naming `offset`" for `offset=-1`; the rule is `offset.bounds`* |

They are not symmetric. `offset` has a rule in the registry; `limit` has none — and
`ApiError.__init__` refuses any code outside the closed list, `Violation` refuses any rule outside
the fourteen. So `?limit=500` has **no representable refusal**. Writing one would be an extension
of a registry that `error_codes.md` states is closed; borrowing `field.type` would emit *"limit
must be an integer, for example 50"* for a value that **is** an integer.

That leaves exactly one question, and it is a 50/50 with no stated answer — the Art IX.3 shape this
document set keeps catching in itself. Two engineers implement opposite behaviour and both pass
their own tests.

## Decision

**A. `limit` is CLAMPED to `[1, 200]`; it is never a 422.** `?limit=500` returns 200 rows and
`"limit": 200` in the response body, so the clamp is **visible in the payload** rather than
silent — a client that asked for 500 can see it got 200 without having to count the array.
`?limit=0` and `?limit=-3` clamp up to 1.

The registry decides this. A rule's absence is not an oversight to be worked around; where the
contract can express a refusal it does, and where it cannot the value is coerced into range.
`limit` is a *pagination hint* — the server has always been free to return fewer rows than asked
for, and returning fewer than a client asked for is not a failure of the request.

**B. `offset` IS a 422, and the bound is checked in the SERVICE, not by `Query(ge=0)`.**
FastAPI's `ge=0` raises `RequestValidationError` with type `greater_than_equal`, and
`validation_exception_handler` maps everything that is not `missing` to `field.type` — so
`?offset=-1` would return *"offset must be an integer, for example 0"*, discharging `NEG-X-12`'s
letter (it names `offset`) while contradicting the rule the contract wrote **for this exact case**.

So the annotation carries the *type* (`?offset=abc` is `field.type`, correctly) and the *value*
rule lives beside the other value rules, where `precedence.order` can rank it: `offset.bounds` sits
twelfth, after `range.floor` and before `filter.exclusive`.

**C. `limit`'s presence in `placeholders.types` stands.** `?limit=abc` is still `field.type` with
*"limit must be an integer, for example 50"*. The clamp applies to integers out of range, never to
things that are not integers — coercing `"abc"` to 50 would silently answer a question the client
did not ask.

## Consequences

- The asymmetry is now **stated** rather than inferred from which rules happen to exist, and
  `test_expenses_list.py` asserts both halves — the clamp echoed in the body, and `offset=-1`
  returning the `offset.bounds` sentence rather than the `field.type` one.
- A future need to refuse an over-large `limit` is a change to the registry, made deliberately,
  with a rule and a message — not a `field.type` pressed into service.
- This is the second time a bound has been implemented by `Query(...)` and had to move into the
  service so the *rule attribution* stayed right. The general form: **FastAPI's validators can
  express the constraint but not the sentence**, and here the sentence is the contract.

---

*Ruled under `SW-ADR-015`.*
