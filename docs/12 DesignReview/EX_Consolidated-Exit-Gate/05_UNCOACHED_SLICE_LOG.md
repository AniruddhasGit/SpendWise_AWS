# 05 — The uncoached slice log

**Seven fresh engineers. No coaching. Frozen documents only.**

Each run was a zero-context agent given one task — *plan the vertical slice "a signed-in person
creates an expense, then loads their dashboard summary", end to end* — and one rule: **you may not
ask anything; if the documents don't tell you, guess, and log the guess.**

Every guess is a document defect. The log, not the plan, is the deliverable.

---

## The numbers

| Run | Guesses | BLOCKING | Already-answered list | Where the findings clustered |
|---|---|---|---|---|
| 1 | **18** | 2 | — | everywhere. *"What does the JSON actually look like?"*, asked eight ways |
| 2 | **21** | 4 | — | **seven were defects introduced by the fix for run 1** |
| 3 | **15** | 3 | — | five were mine; the rest structural |
| 4 | **8** | 2 | 5 | six of eight in **one place** — the error path |
| 5 | **8** | 1 | 30 | every one **inside `contract.json`** itself |
| 6 | **8** | 1 | 37 | inside `contract.json` **and the generator** |
| 7 | **7** | 3 | ~45 | **three were defects introduced in rounds 5 and 6** |

**The Definition of Done was zero. It was never reached.**

---

## What the shape of the curve actually says

The count fell 18 → 7 and flattened. That is *not* a document set converging on completeness. Read
the last column instead:

- **Runs 1–3** found gaps across the whole corpus.
- **Runs 4–6** found gaps in one file.
- **Run 7** found three gaps *that the previous two rounds had created*.

**In five of the seven rounds, at least one finding was a defect introduced by the previous
round's repair.** That is the number that matters. The loop was not converging; it was running at
a roughly constant defect-injection rate, and each repair added surface for the next reader.

The honest reading: **document review found what document review can find, and then started
feeding on itself.**

---

## What only this lane could find

Four review passes — a cross-artifact contradiction sweep, an authority audit, a two-way coverage
matrix, a claimed-but-not-done sweep — ran over the same corpus. Between them they found 21
contradictions **between** documents.

**None of them found any of these**, because every one is invisible until somebody tries to build:

| Found by | What it was |
|---|---|
| slice 2 | **Authentication could never have worked.** `sessions` carries `FORCE ROW LEVEL SECURITY` keyed on `app.user_id`; at the session lookup that GUC is unset, so `current_setting(…, true)` is `NULL` and the query returns **zero rows for every request ever made**. And no document named a token claim holding the user id — a genuine bootstrap deadlock. |
| slice 2 | **There were no `GRANT`s at all.** Every query by the runtime role would have failed `permission denied` — **and `verify_invariants.sql` printed all-green**, because all eight of its checks asked what the role *cannot* do. A boot assertion testing one direction passes happily against a role that is completely inert. |
| slice 3 | `GET /api/expenses/{expense_id}` existed in **no** contract document, while three tests required it — including a SEV-1 case. Three hand-maintained copies of the route table all dropped the same row. |
| slice 5 | `REPEATABLE READ`. `SRC-001 §7.4` asked for one round trip, an ADR split it into three queries, and nothing re-established atomicity — under `READ COMMITTED` a concurrent insert between the headline and the breakdown breaks the sum-to-total invariant. Invisible in every single-user test. |
| slice 7 | `RESTART IDENTITY` appeared **nowhere**. Without it the second test case's categories shift to 17–24 and every `by_category` assertion in the gate payload fails. |
| slice 7 | `SET TRANSACTION ISOLATION LEVEL` raises **`25001`** after `set_config` — two APPROVED records that could not both be executed. |

Every one of these would have been caught in minutes by a Python interpreter and a real
PostgreSQL. A reading agent found them slowly, expensively, and often only after this session had
introduced them.

---

## The three defects the loop caught in its own repairs

Worth recording individually, because they are the argument for the lane and against trusting a
single pass.

**Run 2 — the fix for run 1 was the biggest source of run 2's findings.** Run 1's dominant
complaint was that the PRD specified behaviour in prose for ~2,500 lines and contained one JSON
block. The fix was to hand-write two worked payloads and label them **normative**. Run 2 found,
inside that one section: a missing field five documents assert on, `0` where six documents say
`null`, two category names that do not exist, *"ordered descending"* printed over an array that
is not, two required fields dropped, and the wrong ADR cited for the one number that is never
waivable. **A hand-written example is exactly as driftable as the prose it replaces — and once
labelled normative, it drifts with authority.**

**Run 5 — the frozen source was overridden on a misreading.** A seed block created a third person
and justified it in its own cell as *"`P-ACC-02` refuses to start with zero admins."* `P-ACC-02`
says the application refuses to start when no admin exists **and the variable is unset**. On that
misreading the block overrode `SRC-001` ERRATUM E-6, the Constitution's Art IX.4, and a binary
Bible criterion — **the top of the authority order overridden by a document one level below it**,
inside the artifact built to prevent exactly that.

**Run 7 — the record written to fix run 6 returned zero rows.** `SW-ADR-143 A` set the isolation
level via *"a second session dependency that only the summary route declares."* But
`get_current_user` is router-level, and FastAPI resolves those before a path operation's own
parameters — so `set_config` lands in transaction #1 and every summary query runs in transaction
#2 with no identity. RLS returns nothing. The failure `GOTCHAS.md` calls the worst shape in this
system, produced by faithfully implementing the record written to prevent it.

---

## What the loop built that survives

Each round's repair added a gate one level above the last, and **each was added because the
previous one passed while a real defect walked straight through it**:

| Gate | Catches | Added because |
|---|---|---|
| `adr-status` | a citation of a superseded record | 931 references *resolved*; resolving is not being true |
| `stated-count` | a number typed into prose that has drifted | ten of them had, including the scope article's "22 records" when there were 135 |
| `generated-artifact` | a `GENERATED` banner nobody can execute | `security.sql`'s generator did not exist, and an isolation hole grew under the banner |
| `day-one-value` | a near-miss of `75810` asserted anywhere | it appears in 21 places and nothing verified they agree |
| `route-contract` | a route a test names that the contract lacks | three copies of the route table dropped the same row |
| `contract-refs` | a model or `P-` row cited in the spec that does not exist | 17 models were named and none defined |
| `spec-completeness` | a block of the spec that never reaches its page | `render_request_models` was defined and never called; `--check` printed PASS |
| `amendment-marker` | a changed record that does not say so | Art II.6 was the **only** Constitution rule with no check behind it, and it failed exactly as written |

All **15/15 red-proofed** — each planted, each observed firing, each reverted.

---

## The verdict

**The mechanical gate passes and the sufficiency gate does not.**

Every citation resolves and points at a live record. Every stated count is derived. Eight
artifacts regenerate identically. Fifteen checks fire on a planted violation.

And seven fresh engineers still could not plan one vertical slice without inventing something.

The recommendation this log supports is **not another round.** It is that the remaining defects
are of a kind that building settles and reading does not — and that the next reader after this one
should be a compiler.
