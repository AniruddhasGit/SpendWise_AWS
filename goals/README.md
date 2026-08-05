# goals/ — the unit of work

One goal file = one thing you want built. You write the goal; the session builds it; you stop
whenever you like and `/tt` records exactly where it stopped.

## The loop, every session

```
/ss                    orient — reads the newest handoff, PROGRESS, CLAUDE.md, GOTCHAS,
                       reconciles them against git, and recommends ONE restart point
      ↓
write a goal           copy _TEMPLATE.txt → goals/GOAL_<thing>.txt, or just say it in chat
      ↓
build                  the session works the goal until its Definition of Done is met
      ↓                (stop whenever you want — mid-story is fine, that is what handoffs are for)
/tt                    writes handoffs/HANDOFF_<stamp>_<you>.md, appends PROGRESS.md,
                       commits and pushes to GitHub
```

Next session — **any machine, any Claude account** — starts with `/ss` and is fully oriented from
the repo alone. Nothing lives in a chat history.

## The execution order — run these one at a time

Twelve goals take SpendWise from a frozen requirements document to a ledger the build loop
runs off. **Each one depends on the ones above it**, so they are executed in this order and
the full document is read before the next begins.

| # | Goal file | Produces | Why it sits here |
|---|---|---|---|
| 1 | `GOAL_01_source-of-truth.txt` | `00 SourceOfTruth/SRC-002` | 13 ADRs currently cite a conversation, not a file. Fix the provenance before anything is built on it. |
| 2 | `GOAL_02_adr-completion.txt` | `01 ADR/` new records | Find every decision the BRD and PRD will need. Rule what is rulable; raise the rest. |
| 3 | `GOAL_03_brd.txt` | `02 BRD/` | What and why, in business language. 2–4 pages. |
| 4 | `GOAL_04_design-system.txt` | `05 B DesignSystem/` | Before the PRD, because the PRD's UX section binds to it. |
| 5 | `GOAL_05_prd.txt` | `03 PRD/` | **The document the code is written from.** The largest artifact here. |
| 6 | `GOAL_06_journeys.txt` | `11 Journeys/` | Finds what a per-screen spec misses: the seams between screens. |
| 7 | `GOAL_07_bible.txt` | `05 Bible/` | The scope arbiter. After this, no scope exists beyond an `AcceptanceCriteria` cell. |
| 8 | `GOAL_08_datamodel.txt` | `06 DataModel/` | A package, not a document. Real SQL. The last artifact before code. |
| 9 | `GOAL_09_architecture.txt` | `07 Architecture/` | Two audiences: `for_llm/` to orient a session, `for_humans/` to decide from. |
| 10 | `GOAL_10_sit.txt` | `08 SIT/` | Positive cases, written before the code exists. |
| 11 | `GOAL_11_negative-testing.txt` | `09 NegativeTesting/` | The cases that try to break it. Weighted at user B seeing user A's money. |
| 12 | `GOAL_12_engineering-ledger.txt` | `10 EngineeringLedger/` | What `/ss` reads to report the frontier. Makes cold resumption real. |
| 13 | `GOAL_13_consolidated-exit-gate.txt` | `12 DesignReview/` | **The gate before code.** Do the eight documents agree with each other, and can a stranger build from them? |

Every goal is set to **Opus 5 · xhigh effort · ultracode · maximum parallelism**, and every
one carries a Definition of Done whose lines are binary and name the command that proves them.

Several close on a **fresh zero-context session** grading the output — a session that never
saw the work being made. That is deliberate: the writer never verifies its own work, and where
no second human exists, a session with no inherited context is the substitute.

Two goals are designed to be **failed on the first attempt**: `GOAL_05` (the PRD) does not
close until a fresh session reports fewer than 5 places it would have to guess, and `GOAL_06`
(journeys) treats "found zero defects" as a suspicious result requiring explanation rather
than a good one.

## The two layers of checking

**Every goal runs `tools/consistency_check.py`** as a Definition-of-Done line — the cheap,
mechanical layer. It answers one question: *does every cross-reference actually resolve?*
Dangling ADR ids, dangling `OPEN-` ids, an erratum claimed but never filed, a prep-queue row
claimed but never added. That last class is the **"I reported an action I did not perform"**
breach, and `GOAL_02`'s review spent an expensive adversarial agent finding four of them that
a 40-line script catches instantly.

It ships `--selftest`, which **plants a real violation of each rule and requires the check to
fire** — by delta, so it still red-proofs on a repo that is already red. A check nobody has
watched fail is decoration.

**`GOAL_13` is the expensive layer**, and it exists because the cheap one is blind to the
thing that actually bit us: three contradictions *between* ADRs that each resolved perfectly
well on their own. Plus the uncoached vertical slice — a fresh agent handed the frozen
documents and nothing else, whose every question is a defect in the documents rather than a
failing of the agent.

## Writing a good goal

The template asks for six things. Two of them are what make it work:

**The write-set.** The exact files this goal may touch. Two goals whose write-sets overlap must
never run at the same time — that is how parallel work stays safe, and grouping "by topic" is not
good enough. If the work needs a file outside the list, the session stops and asks rather than
widening quietly.

**A binary Definition of Done.** Every line either passes or fails, and names the command that
proves it. "The dashboard works" is not a DoD. "`GET /api/summary?from=2026-08-01&to=2026-08-31`
returns `daily_average_paise: 75810` against the seeded fixture" is.

## The shortcut

If you don't want to write the goal yourself, paste this and let the session write it for you:

> Build me a goal file for: `<the task>`. Use the template in `goals/_TEMPLATE.txt`, read
> `CLAUDE.md` and `CONSTITUTION.md` first, and make every Definition-of-Done line binary.

Then read it, correct it, and run it. Reading a goal takes a minute; a wrong goal costs an evening.

## Naming

`GOAL_<short-slug>.txt` — e.g. `GOAL_freeze-source-of-truth.txt`, `GOAL_day-one-proof.txt`.
Keep finished ones. They are the record of what was actually asked for, which is not always what
the backlog said.
