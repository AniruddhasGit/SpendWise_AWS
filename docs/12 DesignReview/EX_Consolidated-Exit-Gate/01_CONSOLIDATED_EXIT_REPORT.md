# 01 — Consolidated exit report

**GOAL_13, the pre-code exit gate. 2026-08-05.**

The question this gate answers is not *are the documents consistent* — a script can answer that,
and it did. It is **are the documents sufficient**: can an engineer who has never seen this project
build from them without inventing anything.

Five lanes ran. Four were mechanical or adversarial review. The fifth was the only one that could
answer the actual question, and it is the one that failed.

---

## The headline

| Lane | Result |
|---|---|
| **X-01** cross-artifact contradictions | 21 findings — 4 CRITICAL, 5 HIGH, 9 MEDIUM, 3 LOW. All closed. |
| **X-02** two-way coverage, 8 seams | **8/8 PASS** — no gap, no creep |
| **X-03** authority audit | no build-session ruling breached a reserved matter |
| **X-04** claimed-but-not-done | 5 found, all closed (a matrix ordered and never published, three prep-queue rows asserted and never added) |
| **Exit-gate supersession audit** | 3 of 22 links broken; one had silently withdrawn a live decision |
| **`consistency_check.py`** | **PASS**, 15 checks, **15/15 red-proofed**, 8 generated artifacts verified by regeneration |
| **The uncoached slice** | **7 runs: 18 · 21 · 15 · 8 · 8 · 8 · 7 — never zero** |

**The gate's Definition of Done is zero guesses on a fresh run. That was not reached.**

---

## 1. The defect that mattered most

`docs/06 DataModel/security.sql` contained:

```sql
CREATE POLICY expenses_admin_count ON expenses
    FOR SELECT USING (current_setting('app.is_admin', true) = 'true');
```

A PostgreSQL row-level security policy is **row**-level. It has no column dimension. Permissive
policies for the same command are combined with `OR`. So this policy returned **every column of
every row** — `amount_paise` and `description` included — to any connection with that GUC set.

`SRC-001 §4.5` is the client's stated privacy value: *admins should not see other people's actual
spending.* `P-PRV-02` claimed it was enforced *"structurally"*. It was false at the database.

**No stated test could have caught it.** Every test asserts on the API response shape, and the API
would have kept returning exactly the right fields — from a query that was allowed to read
everything. The defect lived one layer below every assertion in the project.

`SW-ADR-129` replaces it with a `SECURITY DEFINER` function whose **return type** is the guard:
`RETURNS TABLE (expense_count BIGINT, last_activity DATE)`. An amount cannot come back through it
because there is no column for one.

**The general lesson, which is the reason this is finding #1:** a rule expressed in a mechanism
that cannot carry it does not become true by being written carefully. `SW-ADR-077` conceded it in
its own Consequences — *"the reason it is safe is the response shape, not the policy"* — while its
Decision line said "aggregate reads only". Both sentences were in the same record.

## 2. Why it survived

`security.sql` said **"GENERATED from datamodel.json. DO NOT HAND-EDIT"**, and the generator lived
in a scratch directory and was gone. `SW-ADR-066` says a hand patch to a generated file is erased
by the next build — but there was no next build, so **a hand patch simply became the artifact**.
The offending policy appears nowhere in `datamodel.json`, the spec of record.

`fingerprints.json` could not have caught it: it watches for a generated hash **moving**, which is
structurally blind to content the spec never contained.

The banner was the defect's hiding place, so the banner is now executable. `generate.py` lives in
the repository, produces all three artifacts, and `--check` compares **content**. `schema.sql`
round-trips byte-for-byte against the file that existed before, which is the strongest available
evidence the generator is faithful.

## 3. The supersession graph was mis-wired

A topic-coherence audit of all 22 supersession links found three where the successor had no
subject in common with what it replaced. The worst:

**`SW-ADR-088` is a *labelling* record.** Its Decision annotates six ADRs as
`UNVERIFIED — reasoned, not observed`. It named the first of the six in its `Supersedes` field,
and the banner machinery then marked `SW-ADR-023` — **"BIGINT identity on every table"** — as
SUPERSEDED, flipping its ledger status. Every primary key in the schema rests on that decision. It
was **withdrawn by a bookkeeping side effect** and then cited fourteen times as live authority,
which was accidentally the correct reading.

**This repair pass made it worse before it made it better.** It trusted the `Supersedes` field and
re-pointed all fourteen citations to a record about AWS-claim labelling. That is recorded in
`SW-ADR-132` rather than erased: *a repair pass that trusts upstream metadata inherits upstream
defects.*

## 4. Four gates added, all red-proofed

Nine checks existed and passed everything. Each new gate closes a class the nine were structurally
blind to.

| Gate | The class it closes | Why the old nine missed it |
|---|---|---|
| `adr-status` | 80 citations of superseded records, including `CONSTITUTION.md` Art IV.1 resting the product's central security promise on a withdrawn one | check 2 proved 931 references **resolve**. Resolving is not being true. |
| `stated-count` | 10 numbers typed into prose that had drifted — "the 22 records" in the scope article, when there were 135 | no check derived any count; they were prose, and prose was not checked |
| `generated-artifact` | a GENERATED banner nobody could execute | `fingerprints.json` watches a hash move; it cannot see content the spec never had |
| `day-one-value` | the never-waivable `75810`, asserted in 21 places with nothing verifying they agree | recomputes `379049 / 5` half-up from the four fixture amounts |

Each **exempts a document that narrates history or warns about a wrong value**, scoped to the line
— so a record naming what it superseded, or the PRD warning that truncation gives `75809`, does
not fire. The exemptions were themselves red-proofed by planting an un-narrated assertion.

## 5. The uncoached slice — the lane that failed

Three fresh engineers, no coaching, frozen documents only, told to plan one vertical slice and log
every guess.

| Run | Guesses | What it found |
|---|---|---|
| 1 | **18** — 2 BLOCKING | the `app.is_admin` contradiction; forged `user_id` 201-vs-404; and one request repeated eight times: *what does the JSON actually look like?* |
| 2 | **21** — worse | **seven of them were defects introduced by the fix for run 1**, plus two BLOCKING gaps nobody had seen |
| 3 | **15** | five were mine; `GET /api/expenses/{expense_id}` in no contract document |
| 4 | **8** | six of eight in one place — the error path |
| 5 | **8** | every one inside `contract.json`; one overrode the frozen source on a misreading |
| 6 | **8** | `render_request_models` defined and never called; two ADRs that cannot both execute |
| 7 | **7** | three were defects introduced in rounds 5 and 6 |

**In five of the seven rounds, at least one finding was a defect introduced by the previous
round's repair.** The loop was not converging — it ran at a roughly constant defect-injection
rate. Full data in `05_UNCOACHED_SLICE_LOG.md`.

**Run 2 is the most valuable result this gate produced**, because it is the one that indicts the
method rather than the artifact.

Run 1's dominant complaint was that the PRD specified behaviour in prose for ~2,500 lines and
contained one JSON block. The fix was to hand-write two worked payloads and label them
**normative**. Run 2 read that section and found, inside it alone: a missing field that
`SRC-001 §7.4` requires and `SIT-E0-S9-05` asserts on by a name that did not exist; `0` where six
documents say `null`; a gate range contradicting the ADR and the executable test; two category
names that are not on the ruled list; "ordered descending" printed over an array that is not; two
required fields dropped; and the wrong ADR cited for the one number the project cannot get wrong.

**A hand-written example is exactly as driftable as the prose it replaces — and once labelled
normative, it drifts with authority.**

`SW-ADR-138` makes the API contract a **generated** artifact: `contract.json` is the spec of
record, and `expected_summary.json`, the error-code registry and PRD §6.1/§6.2 are computed from
it. The generator **asserts the gate before writing anything** — if the spec ever computes an
average other than `75810` from its own fixture, it exits non-zero and emits nothing. The ordering
contradiction is not fixed; it is made **unrepresentable**, because the example is produced by the
rule.

Run 2 also found two BLOCKING gaps that three prior review passes had missed:

- **Authentication could never have worked.** `sessions` carries `FORCE ROW LEVEL SECURITY` with a
  policy on `app.user_id`. At the moment of the session lookup the GUC is unset, so
  `current_setting(…, true)` is `NULL` and the lookup returns **zero rows for every request ever
  made**. And no document named a token claim holding the user id, so there was nothing to set the
  GUC from — a genuine bootstrap deadlock, not an ordering preference. (`SW-ADR-136`)
- **There were no table grants at all.** Every query by the runtime role would have failed with
  `permission denied` — **and `verify_invariants.sql` would still have printed all-green**, because
  all eight of its checks asked what the role *cannot* do. A boot assertion that tests one
  direction passes happily against a role that is completely inert. (`SW-ADR-137`)

## 6. What this gate does not certify

**Not one line of application code exists.** No database has been created. The day-one proof — the
`75810` assertion watched by a named human — has not been run. Every claim here is document
against document.

The `expenses_admin_count` analysis is reasoned from documented PostgreSQL semantics, **not
observed**. `NEG-X-21` exists to settle it against a real instance, by re-adding the old policy and
watching the case go red. Until that runs, `SW-ADR-129` should be read as provisional on it.

Every AWS claim is `UNVERIFIED — reasoned, not observed` (`SW-ADR-005`, `SW-ADR-088`). This session
never touched AWS and never will.

`08_REVIEWER_SELF_CHALLENGE.md` is the case against this report, including the one place the
adversarial reviewer was **wrong** — it reported the BRD holds 77 requirements; it holds 76, with
exact set equality against the PRD coverage map, and `CLAUDE.md` had been right all along.

---

## Verdict

**The mechanical gate passes and the sufficiency gate does not.**

Every seam has two-way coverage. Every citation resolves *and* points at a live record. Every
stated count is derived. Eight artifacts are verified by regeneration. Twelve checks fire on a
planted violation.

And three fresh engineers still could not build one vertical slice without inventing things.

That gap is the finding. It is also the argument for the lane: four review passes over the same
corpus found 21 contradictions between documents, and **none of them found that authentication
could not work or that the runtime role had no privileges** — because both are invisible until
somebody tries to build.
