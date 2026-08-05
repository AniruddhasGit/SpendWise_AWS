# SW-ADR-143 — Isolation is set at checkout, and a generated block must reach its page

> **⚠ DECISION A AMENDED 2026-08-05 by `SW-ADR-144 A`.** A names "a second session dependency
> (`get_db_rr`) that only the summary route declares" and stops there. **Implemented literally it
> opens TWO transactions**: `get_current_user` is a router-level dependency, FastAPI resolves those
> before a path operation's own parameters, so `set_config` lands in transaction #1 and every
> summary query runs in transaction #2 with no `app.user_id` — RLS returns **zero rows**.
> `SW-ADR-144 A` puts one session on `request.state.db` and resolves the level from a route table.
> Decisions B–E stand.
>
> *Found by the seventh uncoached slice. This banner is required by Art II.6 and is now enforced by
> the `amendment-marker` check, which fired on this very record before it was written.*

| Field | Value |
|---|---|
| ADR | `SW-ADR-143` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — (it makes `SW-ADR-136 B` and `SW-ADR-142 F` co-executable) |
| Amends | `SW-ADR-141` (Decision C, the precedence tie-break) |
| Raised by | GOAL_13 uncoached slice run 6 |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-136` · `SW-ADR-141` · `SW-ADR-142` · Art II.1 |

## Context

The sixth uncoached slice logged eight guesses and listed **thirty-seven** candidates it checked
and did not log. It also did what no earlier run did: it verified `contract.json`'s cells against
the documents they cite, one by one, and reported which were true. Three were not.

**1. Two APPROVED records could not both be executed.**

`SW-ADR-136 B` makes `SELECT set_config('app.user_id', …)` the **first statement** of the request
transaction. `SW-ADR-142 F` requires **`REPEATABLE READ`** on any request that reads the summary.
PostgreSQL rejects `SET TRANSACTION ISOLATION LEVEL` after any query in the transaction —
**SQLSTATE 25001**, *"must be called before any query"*.

Executed literally, the summary either 500s on every request or silently stays `READ COMMITTED`,
which is the exact intermittent breakage of the sum-to-total invariant that F was written to
prevent. Two same-rank APPROVED records, written the same day, by this session — the shape
`OPEN-MIGRATE-01` was escalated for.

**2. `SW-ADR-141` asserted a section that did not exist.** It says the request models are
*"rendered as PRD §6.4"*. `render_request_models()` was **defined and never called**. There was no
§6.4, and `generate_api.py --check` printed `PASS` — because it compares the PRD against *what the
generator emits*, never against *what the spec contains*.

**3. `render_codes()` read four keys of the five-key `precedence` object.** The `scope` block —
the paragraph that stops `field.required` from making `range.required` unreachable — existed in
`contract.json` and reached no page. The registry a reader was pointed at stated an order and
omitted the only text that makes it correct.

Every reference in both cases **resolved**. `contract-refs` is a reference check and both slipped
straight past it.

## Decision

**A. The isolation level is selected on the connection at checkout, before `BEGIN`** — a second
session dependency (`get_db_rr`) that only the summary route declares. `set_config` remains the
first *statement* inside the transaction, so `SW-ADR-136 B` holds and `SW-ADR-142 F` holds.
**Reasoned, not observed** — no database has been run.

**B. The `last_seen_at` heartbeat runs inside its own `SAVEPOINT`.** `SW-ADR-142 F` put a *write*
inside a serialisable snapshot. Two concurrent requests on one session that both see the timestamp
stale will both `UPDATE` it, and under `REPEATABLE READ` the loser gets **40001** and the request
dies — where `READ COMMITTED` would simply block and succeed. `J-U-09` documents the dashboard
firing several requests at once, so this is a 500 on the dashboard, intermittently, in production
only. On `40001` the savepoint is rolled back and the request continues: losing one bump is
harmless, because the transaction that won already performed it.

**C. `consistency_check.py` gains `spec-completeness`** — for each block of the spec of record,
assert its entries actually **appear** in the artifact it claims to feed. Not a reference check: a
**completeness** check. On the day it was written it verified 105 entries across 9 blocks.

> `SW-ADR-138`: a hand-written payload drifts, so generate it.
> `SW-ADR-142`: a hand-written citation drifts, so resolve it.
> **This record: a hand-written *generator* drifts too — and the thing checking it is the same
> program.**

**D. Ten codes get a message.** `messages.rules` covered the `VALIDATION_ERROR` rules only, so
five codes had no stated sentence — in a registry whose own note says *"the rendered sentence is
what a test asserts on"*, and while `ACCOUNT_DEACTIVATED`'s exact wording was specified by
`SW-ADR-100` and `P-ACC-07`'s four outcomes word for word. `SESSION_INVALID` gets **one** sentence
for every cause: distinguishing expiry from a bad signature would tell an attacker which they hit.

**E.** `range.required` names `from` when **both** parameters are absent — the most likely
malformed summary request there is, and both the rule and its scope cell were phrased in the
singular. The precedence tie-break defers to the **request model's** declaration order, not
§6.1's, because the model is what the code is built from and Pydantic reports in declaration
order. Types are **strict**, the only coercion being ISO-8601 text to `date`. Plus `CV-24`
(per-test reset is truncate-and-reseed, because the usual outer-transaction-rollback pattern
breaks a transaction-local GUC), `CV-25` (truncate a timestamp, never round — rounding can carry
across a day boundary), `CV-26` (`Cache-Control: no-store`, because the deployment has no TLS and
a cached summary is a cross-person leak achieved without touching the database).

## Consequences

- **The PRD's own header says "this is the document the code is written from."** Twelve request
  models — the half of the contract every 422 test touches — were absent from it while the ADR
  that created them said otherwise. Both blocks now reach the page and a check asserts it.
- The patch script that was supposed to wire §6.4 printed *"§6.4 wired in"* while its replacement
  silently failed to match. That is the **claimed-but-not-done** class, in the tooling built to
  catch it, for the third time this session. It is recorded rather than tidied away.
- Six uncoached runs: **18 → 21 → 15 → 8 → 8 → 8**. The count is flat and the "already answered"
  list has grown 5 → 30 → 37. What remains is concentrated in one file and one program, and both
  are now checked.

---

*Ruled under `SW-ADR-015`. It supersedes nothing; it makes two records co-executable.*
