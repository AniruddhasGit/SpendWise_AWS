# 08 — Reviewer self-challenge

*Art VII: the writer never verifies its own work. This document is the exception being
declared rather than hidden — the session that made the repairs is also the session reporting
them, so here is the case against its own report.*

---

## 1. The reviewer was wrong at least once, and it was caught by counting

X-01 reported **FINDING-14**: `CLAUDE.md` claims 76 BRD requirements, the artifact holds **77**,
and the PRD coverage map "agrees: 77 BRD rows, all covered".

It holds **76**. Counted directly: 76 distinct row ids in the BRD, 76 in the PRD coverage map,
**exact set equality, zero in either that is not in the other**. `CLAUDE.md` was right and the
PRD's "77" was the error — the reverse of what was reported.

This matters more than the number. Twenty-one findings arrived in a confident, well-evidenced
report, and one of them was backwards. **Every count in this exit gate was recomputed rather than
accepted**, and this is the one that moved. A second finding (`X-01 FINDING-1`) rested on
PostgreSQL semantics the reviewer explicitly flagged it could not execute — see §3.

## 2. The repair pass propagated a defect before catching it

`SW-ADR-088`'s `Supersedes` field named `SW-ADR-023`. The repair pass trusted that field and
re-pointed **fourteen** citations from `SW-ADR-023` to `SW-ADR-088` — from "Primary keys are BIGINT
identity columns" to "AWS claims in build-session ADRs are labelled reasoned, not observed".

It was caught by the `citation-topic` heuristic firing on the *result*, which prompted a
topic-coherence audit of all 22 supersessions, which found three broken links including this one.
`SW-ADR-132` records it. The point stands unflattered: **a repair pass that trusts upstream
metadata inherits upstream defects**, and this one did, for about twenty minutes.

## 3. What is still reasoned rather than observed

- **The isolation hole.** That `expenses_admin_count` returned every column of every row is
  derived from documented PostgreSQL semantics — permissive policies for the same command are
  combined with `OR`, and RLS is row-level with no column dimension (column restriction requires
  `GRANT SELECT (col)`, which nothing here used). **No database was run.** It is a strong
  documentary argument, not an observation. `NEG-X-21` exists to settle it against a real
  instance, and `SW-ADR-129` should be treated as provisional on that case going red with the old
  policy re-added.
- **Every AWS claim.** `SW-ADR-005` holds: this session never observed the application running in
  AWS. `SW-ADR-088` labels the AWS-touching claims `UNVERIFIED — reasoned, not observed`.
- **`admin_expense_stats()` has never been executed.** The SQL is written, not run. `SET
  search_path` is included because a `SECURITY DEFINER` function without it is a
  privilege-escalation vector — also reasoned.

## 4. What the machine gate cannot see, by construction

`consistency_check.py` passes with **12/12 red-proofed**. That is worth exactly what it claims:

- It proves **931 ADR references resolve** and, since 2026-08-05, that **none rests on a
  non-APPROVED record**. It cannot prove a resolving citation is *about the right thing* —
  `citation-topic` is a keyword heuristic that reports into a review channel and **deliberately
  does not gate**, because a paragraph may legitimately discuss two records.
- It proves **12 stated counts** match the artifacts. It has no opinion on counts nobody wrote down.
- It proves **4 generated artifacts** regenerate identically. It cannot tell you the generator is
  *correct* — only that the committed file is what the generator produces. `schema.sql` round-trips
  byte-for-byte against the pre-existing file, which is the best available evidence and is not proof.
- **It has never seen a line of application code**, because none exists. Every claim downstream of
  the documents is document-against-document.

## 5. Where the numbers in this gate could still be wrong

- ~~**`75810` paise** is asserted in nineteen places and nothing verifies they agree.~~
  **Closed while writing this document.** Writing the gap down made it obvious it was cheap to
  fix, so check 11b now recomputes `379049 / 5` half-up from the four fixture amounts and fails on
  any *asserted* near-miss — while exempting a document that **warns** about the wrong value, which
  the PRD's worked payloads deliberately do (`75809` from truncation, `94762` from dividing by the
  row count). The exemption is scoped to the **line**, not a character window, so unrelated prose
  two paragraphs away cannot excuse a bare assertion. Red-proofed.
  *Recording this rather than silently editing §5: the first draft of this self-challenge listed it
  as a known gap, and a self-challenge that quietly fixes what it was about to admit is worth less
  than one that shows the sequence.*
- **The 25-route coverage matrix** asserts every route has at least one cross-person case. The
  mapping from route to case was authored, not derived from the case rows — a case id could name a
  route it does not actually exercise, and nothing checks that.
- **`generate.py` reproduces Alembic's naming convention** by reimplementing it. If the real
  `MetaData` convention differs, the DDL and the ORM will disagree at the first migration. Nothing
  verifies this until Alembic runs.

## 6. The honest summary

The document set went from **one live isolation hole, three broken supersession links, 80 stale
authority citations and ten drifted counts** to a state where all of those are closed and **four**
new gates fire on a planted violation.

It has still never been executed. **Not one line of application code exists**, no database has been
created, and the day-one proof — the `75810` assertion watched by a named human — has not been run.
Everything here is a claim about documents, checked against other documents. That is the whole of
what this gate certifies, and the value of the uncoached slice is that it is the only lane that
tests whether the documents are *sufficient* rather than merely *consistent*.
