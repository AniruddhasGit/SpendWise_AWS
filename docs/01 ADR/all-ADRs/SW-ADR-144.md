# SW-ADR-144 — One session, one transaction; and Art II.6 gets a check

| Field | Value |
|---|---|
| ADR | `SW-ADR-144` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | `SW-ADR-143` (Decision A, which named a second dependency and stopped there) |
| Raised by | GOAL_13 uncoached slice run 7 |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-136` · `SW-ADR-141` · `SW-ADR-142` · `SW-ADR-143` · `SRC-001 §4.3` · Art II.6 |

## Context

The seventh uncoached slice logged **seven** guesses — the first fall since run 4 — and found
three BLOCKING defects, two of which this session had created in the previous two rounds.

**1. `SW-ADR-143 A` produces two transactions, and the summary returns nothing.**

It said the isolation level is chosen by *"a second session dependency (`get_db_rr`) that only the
summary route declares"*, and stopped there. But `get_current_user` is a **router-level**
dependency — `SRC-001 §4.3` requires it written once and applied to the whole router — and FastAPI
resolves router-level dependencies **before** a path operation's own parameters.

So `get_current_user`'s session opens first at `READ COMMITTED`, `set_config` lands in **that**
transaction, and `get_db_rr` then opens a **second** one. Every summary query in transaction #2
has no `app.user_id`, so RLS returns **zero rows** — the failure `GOTCHAS.md` calls the worst
shape in this system, produced by faithfully implementing the record written to prevent it.

**2. Five validation rules fired on a model that did not exist.** `range.required`, `range.order`,
`range.span`, `range.floor` and `filter.exclusive` apply only to the summary's query pair, and
`precedence.tie_break` resolves same-class collisions by *"the order the request model declares
them"*. There was no `SummaryQuery`. `?from=x&to=y`, both failing `field.type`, had no stated
expected `field`. `NEG-X-12` (SEV-1) requires *"422 naming `offset`"* and the closed
fourteen-rule registry contained **no rule capable of producing it**.

**3. `CV-24`'s per-case truncate had no role and no `RESTART IDENTITY`.** `spendwise_app` holds no
`DELETE` on `users` and `verify_invariants.sql` check 11 asserts it *cannot* — so the runtime role
cannot perform the reset, and nothing said which connection does. And a plain `TRUNCATE` does not
reset a `GENERATED ALWAYS AS IDENTITY` sequence: without `RESTART IDENTITY` the second test case's
person A gets categories 17–24, and **every `by_category` assertion in `expected_summary.json`
fails**. That phrase appeared nowhere in the document set.

**4. And the one this record is named for.** `SW-ADR-141 C` says the tie-break is *"§6.1's worked
payload order"*. `SW-ADR-143 E` says it is the **request model's declaration order**. Both
APPROVED, both live, `SW-ADR-141` **unmarked**. `CONSTITUTION.md` Art II.6: *"Superseded text MUST
be marked superseded where it stands. An unmarked contradiction between two live documents is a
defect, not a reader's judgement call."*

An engineer resolving `error_codes.md`'s dangling *"(see `tie_break`)"* the way this document set
trains them to — by going to the ADRs — finds `SW-ADR-141 C` and implements the wrong order. **And
every negative case still passes**, because, as `precedence.note` itself says, each varies exactly
one input. Two engineers ship opposite behaviour and both go green: the Art IX.3 failure,
reproduced inside the block written to end it.

## Decision

**A. One session factory, one `AsyncSession`, one transaction, held on `request.state.db`.**
`get_db` and `get_db_rr` both delegate to it; a second call asking for a *different* isolation
level **raises** rather than silently reusing the wrong one. The level is resolved from a
module-level `REPEATABLE_READ_ROUTES` table consulted by the factory — never from
dependency-resolution order — with a **boot assertion that fails closed** if the declared markers
and the table disagree.

**B. `SummaryQuery` and `ExpenseListQuery` join the request models**, and `offset.bounds` joins
the registry with its message, discharging `NEG-X-12`.

**C. `CV-24` names the role and the statement**: an owner-role connection **owned by the test
fixture**, `TRUNCATE … RESTART IDENTITY CASCADE`. Fixture-owned so that `seed/README.md`'s rule —
*"the seeder does not acquire a user-deletion path by the back door"* — still holds of the seeder.

**D. `SW-ADR-141` carries a banner naming `SW-ADR-143 E`**, and an `Amends` row is now part of the
record format.

**E. `consistency_check.py` gains `amendment-marker`.** An ADR that declares `Amends: X` fails the
build unless **X carries a banner naming it**. Art II.6 was the only rule in the Constitution with
no automated check behind it, and it failed exactly as written.

**F. `spec-completeness` becomes per-KEY, not per-block.** `precedence` rendered four of its five
keys and the block still looked covered, so the tie-break reached no page while the page printed a
pointer to it. Rationale keys (`why*`, `note`, `alternative`) must reach *some* document rather
than a specific table — an unpublished rationale is how this contradiction stayed invisible.

## Consequences

- **Three checks in three rounds, each one level up:** `contract-refs` (a citation resolves),
  `spec-completeness` (a block reaches its page), `amendment-marker` (a changed record says so).
  Each was added because the previous one passed while a real defect walked through it.
- The per-route `error_codes` arrays are **route-specific**; `BAD_REQUEST`, `RATE_LIMITED` and
  `INTERNAL` are reachable everywhere and are stated once rather than repeated.
- Seven uncoached runs: **18 → 21 → 15 → 8 → 8 → 8 → 7**, with the already-answered list at
  ~45. Three of run 7's seven were defects this session introduced in rounds five and six — which
  is the argument for continuing to run it, not for stopping.

---

*Ruled under `SW-ADR-015`.*
