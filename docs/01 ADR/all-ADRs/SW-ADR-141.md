# SW-ADR-141 — The error path joins the spec of record

> **⚠ DECISION C AMENDED 2026-08-05 by `SW-ADR-143 E`.** The tie-break below says *"then
> fields in the order §6.1's worked payload lists them"*. It is **the order the REQUEST
> MODEL declares them** — `request_models.<Model>.fields`. The two differ whenever
> `spent_on` competes with `category_id` or `description` in one rule class, and Pydantic
> reports in declaration order, so the natural implementation silently produced the other
> answer. Every other decision in this record stands.
>
> *This banner exists because the seventh uncoached slice found the contradiction. Art II.6
> required it from the moment `SW-ADR-143` was written, and Art II.6 was the one rule in
> the Constitution with no automated check behind it. There is one now.*

| Field | Value |
|---|---|
| ADR | `SW-ADR-141` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice run 4 |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-138` · `SW-ADR-140` · `SW-ADR-051` · Art IX.3 |

## Context

The fourth uncoached slice logged **eight** guesses, down from eighteen, twenty-one and fifteen.
It also did something none of the earlier runs did: it listed five candidates it had checked and
**deliberately did not log**, because they were already answered.

**Six of the eight were in one place — the error path.**

`SW-ADR-138` pulled the *response* models into a generated spec of record, because hand-written
payloads drift. `SW-ADR-140` created the message registry with exactly the right argument:
*"'422 naming the cap' is a binary assertion on a string nothing specified."*

That argument was applied to eleven **value** rules and then stopped. It applies identically to
*"amount is missing"*, *"spent_on is not a date"*, and *"two rules failed — which one do I
report?"* — and those are more common in real traffic than every value rule combined.

`ExpenseCreate` and `Principal` appeared in the route table as bare strings and were **defined
nowhere**. The request models are half the contract and every 422 test touches them.

## Decision

**A. `request_models` joins `contract.json`.** `ExpenseCreate`, `ExpenseUpdate` and `Principal`,
each field with its type, whether it is required, and what happens to it. Rendered as PRD §6.4.

**B. Two rules join the message registry**: `field.required` and `field.type`, with a placeholder
table (`{field}`, `{expected}`, `{example}`) — because the *rendered sentence* is what a test
asserts on, so the substitutions are part of the contract.

**C. Validation precedence is stated and short-circuits.** Presence → type → value, then fields in
the order §6.1's worked payload lists them, with `category.not_owned` last because the database
raises it after every in-process rule has passed.

> Without this, a body that breaks two rules has a **50/50** expected value. Two engineers
> implement opposite orders and both pass their own tests — the Art IX.3 failure exactly: an
> acceptance criterion that is not binary. Every negative case varies exactly one input, so
> nothing in the suite forced the question.

**D. Three one-line holes the models left**, each invisible until it is not:

- `Expense.category_name` is **`null`** when `category_id` is null. The `Uncategorised` label
  belongs to `CategoryBucket` alone — on an expense row it would make a synthetic display string
  indistinguishable from a real category name. **Day one exercises this**: the seed's fourth
  expense has no category.
- `CategoryBucket.percent` divides by the **sum of the buckets**, not the headline `total_paise`.
  Identical under no filter; under a category filter the headline re-scopes and `by_category` does
  not, so dividing by the headline would print percentages summing to several hundred.
- `SESSION_INVALID` covers a token that is **otherwise unverifiable** — a bad signature,
  `alg=none`, a broken structure. The registry is closed and a tampered token fitted no entry.

**E. `contract.json` no longer claims to generate an `openapi.yaml`.** It never did. That was a
false claim inside the one document whose stated purpose is to be the place that cannot drift, and
`--check` could not catch it because it does not check for a file it never writes.

## Consequences

- **`P-UND-06` is corrected in the same pass** (slice C1). It read *"average null"* beside *"the
  full day series of zero-valued days"*, and those cannot both hold — a full series means time has
  elapsed, and the formula then yields **0**. `SW-ADR-053` states the rule with the qualifier
  *when elapsed is zero*; the PRD sentence dropped it. Built as written, a new account opening
  1–31 August on the 5th renders **₹0.00** where `P-UND-02` requires an em-dash — on the first
  screen every new user sees.
- `NEG-M-06` said *"422 **or** exact-decimal handling"*. A disjunction is not a binary criterion
  (Art IX.3). It is 422.
- `NEG-X-12`'s title named *"A's summary with a manipulated cursor"* while its request was
  `GET /api/expenses?offset=-1`. The summary has no pagination of any kind; following the title
  would have meant inventing one.
- **The convergence is the finding.** 18 → 21 → 15 → 8, with the residue concentrating in one
  area rather than scattering. That is what a document set closing looks like — and run 2's
  *increase* is the reason to trust the trend, because it caught the repair introducing defects.

---

*Ruled under `SW-ADR-015`. It supersedes nothing.*
