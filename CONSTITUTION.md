# SpendWise Project Constitution

| Field | Value |
|---|---|
| Version | v0.1-draft |
| Decision status | **NOT_DECIDED** (fail-closed — binds nothing until ratified) |
| Release status | NOT_RELEASED |
| Ratifier | the client — exact name pending `OPEN-NAME-01` |
| Drafted | 2026-08-05, from `docs/00 SourceOfTruth/SRC-001` and the 22 records in `docs/01 ADR/` |
| Governs | the SpendWise build and the use of this repository |

---

## Preamble

This is the single short document of **non-negotiable principles** for SpendWise. Every
specification, plan, ADR, backlog row and implementation is checked against it.

**It invents nothing.** Every binding article consolidates a rule that already binds — from the
frozen source `SRC-001`, from an `APPROVED` row in the ADR ledger, or from an explicit client
ruling — and cites where it came from. Where a decision is still open, Article X lists it as open
and deliberately does not decide it.

This document is a **gate, not a spec.** The cited sources carry the full detail.

### Reading rules

- **MUST / MUST NOT** items bind on ratification.
- **(build-session ruled)** items were decided by the build session under `SW-ADR-015`'s standing
  delegation. They bind, and the client may reverse any of them at any time.
- **(unverified)** marks a claim the build session has not observed. Under Article VII it may never
  harden into a `MUST`.

---

## Article I — Scope

1. **The functional envelope is `docs/00 SourceOfTruth/SRC-001` plus the 22 records in
   `docs/01 ADR/all-ADRs/`.** No user-facing functionality beyond those two locations.
   Envelope ≠ approval: Article III still controls what is approved to *build*.
2. **Hard exclusions** (`SRC-001 §12`) MUST NOT enter scope: no native mobile app; no reading bank
   SMS; no Account Aggregator or bank API integration; no pulling from Google Pay or Blinkit.
3. **Deferred, not cancelled** (`SRC-001 §14`): bank-statement CSV import, the web app manifest,
   note autocomplete, editing an expense in the UI, per-category budgets. The expense-update
   *endpoint* exists in v1; its *screen* does not.
4. Any "can it also…" request is a **scope change only the client decides.** A reviewer, a test run
   or a fresh agent cannot authorise scope.
5. **Win condition — define victory, then stop.** A person signs up, logs an expense and sees a
   correct dashboard; a second person cannot see the first person's money, proven at the database
   layer; an admin can reset a password and force a sign-out; it runs on AWS from a container the
   client deployed by hand. Everything past that line is fast-follow.

## Article II — Authority Order & Sources

1. **On conflict, resolve in this order:** raw `SRC-001` wording → an explicit client ruling →
   an `APPROVED` ADR → `03 PRD` → `02 BRD` → `05 Bible` → everything else.
   **Stricter always wins.**
2. `SRC-001` is a **frozen input.** It MUST NOT be edited. The only permitted modification is a
   clearly-marked `ERRATUM` block appended at its foot.
3. **Errata govern over the text they correct.** Seven exist (`E-1`…`E-7`), each citing the ADR
   that ruled it.
4. **Fingerprints are the evidence of record.** `docs/00 SourceOfTruth/fingerprints.json` holds a
   SHA-256 per frozen source. If a hash changes, every artifact derived from that source is
   **invalidated and MUST be re-derived**, never silently reused.
5. **Derived content MUST cite a source or carry an explicit `ASSUMED` flag.** `ASSUMED` is
   inference, never authority, and MUST NOT be promoted into a `MUST` rule.
6. Superseded text MUST be **marked superseded where it stands.** An unmarked contradiction between
   two live documents is a defect, not a reader's judgement call.

## Article III — Decision & Release Governance

1. The decision authority of record is **`docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv`**.
   Decisions are **fail-closed**: every new ADR starts `NOT_DECIDED` + `HOLD_PENDING_DECISION` +
   `NOT_RELEASED`. **Silence never counts as approval, retirement, or release.**
2. Accepted decisions are **immutable.** A reversal happens by a new superseding record, never by
   editing history. `SW-ADR-004` is the worked example — superseded by `SW-ADR-008` one hour later,
   retained unedited and marked.
3. The ledger's four `included_in_*` columns are the **anti-drift mechanism**: a decision is not
   merely decided, it must be shown to have *landed* in the BRD, PRD, Bible and data model. Flip a
   cell to `INCLUDED` only with the carrying section cited in `notes`. **All 22 rows read
   `NOT_INCLUDED` today**, correctly — those documents do not yet exist.
4. **Credentials MUST NEVER appear in an ADR, the ledger, or any committed file.**
5. **Status law**, applied to every schema, API and specification artifact:

   | Status | Meaning |
   |---|---|
   | `RULED` | decided, with a citation to `SRC-001` or an `APPROVED` ADR |
   | `PROVISIONAL` | written down, a ruling still outstanding |
   | `OPEN` | genuinely unruled — **escalate, never invent** |
   | `ASSUMED` | inference; never hardens into a constraint |

## Article IV — Security & Isolation Floors

1. **Per-user isolation is enforced twice** (`SW-ADR-018`): every query filters on the user id from
   the verified token, **and** Postgres row-level security enforces it at the database.
   A controller-only check is the classic false green and does not satisfy this article.
2. `FORCE ROW LEVEL SECURITY` MUST be on for every protected table. A table's owner bypasses RLS
   otherwise, silently.
3. **The runtime database role MUST NOT own the tables, MUST NOT be superuser, and MUST NOT hold
   `BYPASSRLS`.** Verified by querying the catalog — never assumed.
4. The isolation gate MUST be **red-proofed**: the policy is disabled on purpose, the denial test is
   watched going red, then reverted and the revert verified. A gate nobody has watched fail is
   decoration.
5. Session cookies: **httpOnly, SameSite=Lax**; `Secure` driven by an environment variable.
   `SW-ADR-014` removed the load balancer, so the deployed environment has no TLS — that
   environment is **never called production in any document**, and the weakness is recorded, not
   defaulted into.
6. bcrypt cost 12, run off the event loop; the comparison runs even for an unknown email so timing
   reveals nothing (`SRC-001 §10.5`).
7. Password reset tokens: hashed at rest, single use, one-hour expiry, and **every session of that
   user revoked in the same transaction** (`SRC-001 §5.5`).
8. **No f-strings anywhere near SQL.** SQLAlchemy expression language throughout; if `text()` is
   unavoidable, bind the parameters (`SRC-001 §10.3`).
9. Receipt keys are `receipts/{user_id}/{expense_id}/{uuid}.{ext}` and the server refuses to attach
   a key whose prefix does not match. The bucket blocks all public access; signed URLs expire in
   five minutes (`SRC-001 §8.3`).

## Article V — Money

1. **Integer minor units. Never a float.** Parsed with `Decimal` at the boundary, converted to `int`
   paise in a Pydantic validator, converted back to a display string in React at render time only
   (`SRC-001 §10.1`).
2. **`SUM()` MUST be cast to `BigInteger`** — Postgres returns the sum of a bigint column as
   `numeric`, which arrives as a `Decimal` and mixes badly with `int` (`SRC-001 §10.6`).
3. v1 is **INR only**; currency is snapshotted onto each expense row at write time (`SW-ADR-013`).
4. The daily average is **total ÷ days elapsed, capped at today**, rounded half-up
   (`SW-ADR-010`). The agreed acceptance value is **75,810 paise** against the seeded fixture.
5. **Project spend is reserved to the client.** No model decides it at any confidence, and no
   timeout defaults past it. `SW-ADR-014` fixes the posture at **nothing paid**.

## Article VI — Privacy

1. **Admins MUST NOT see any other user's amounts or descriptions.** Admin surfaces show counts and
   dates only (`SRC-001 §4.5`). Changing this requires a superseding ADR, not a pull request.
2. **Every admin action writes to the audit log in the same transaction as the change.** If the log
   write fails, the change rolls back (`SRC-001 §10.8`).
3. Deleting a user cascades to their categories, expenses and sessions — **and never to the audit
   log**, whose whole purpose is to survive (`SRC-001 §6.9`).
4. **(build-session ruled)** Deleting a user leaves their receipt objects orphaned in S3.
   Recorded as `OPEN-DELETE-01`, not silently accepted.

## Article VII — AI Agent Guardrails

Every session, human or model, is bound by these. They are the honesty floor.

1. **No invented evidence.** Never state a test passed unless it executed and passed. A paper
   exercise is labelled a paper exercise everywhere, including commit messages. **Unverified means
   writing the word "unverified".**
2. **Report what happened.** Worst number first. Every rate carries its count — "31 of 34 passed",
   never "most passed".
3. **A gap stays a gap.** An unknown becomes an `OPEN` row, never a plausible guess. This is the
   rule under most pressure on a single-person project, because the person who could answer is
   always right there and assuming is always faster.
4. **Respect one-way doors.** When unsure whether something can be undone, treat it as though it
   cannot.
5. **The log is the memory.** An unlogged decision is a protocol failure even when the decision was
   right.
6. **Scope as written.** If it cannot be delivered as specified, deliver what can be and say plainly
   what was left out and why.
7. **The writer never verifies its own work.** Where no second human exists, the substitute is a
   **fresh zero-context session** — and the substitution is recorded in the finding, because a
   fallback is only legitimate when it is visible.

## Article VIII — Operations & Deployment

1. **The build session writes application code only.** No pipeline files, no infrastructure-as-code,
   nothing created in AWS (`SW-ADR-005`). The client builds DEV, UAT and PROD by hand.
2. In exchange the build session MUST give **advance notice** of every AWS dependency, early enough
   to be prepared while code is still being written.
3. **The build session never observes the app running in AWS.** Every claim it makes about AWS
   behaviour is **reasoned, not observed**, and MUST be labelled that way.
4. Target (`SW-ADR-014`): ECS on EC2 free tier · **no load balancer** · **no NAT gateway** ·
   SSM Parameter Store · public subnet with a locked-down security group. ECR, RDS, S3 and the two
   IAM roles of `SRC-001 §11.5` are unchanged.
5. Migrations run at container start, behind an **explicit `pg_advisory_xact_lock`** — Alembic takes
   no such lock on its own (`SW-ADR-019`).
6. Configuration arrives through environment variables and a typed `BaseSettings` that **fails
   fast**. A missing required key aborts startup; the dependent story is `Blocked`, never stubbed.
7. **Destructive actions are always human.** No session deletes a database, drops a bucket, or
   rotates a credential.

## Article IX — Quality & Verification

1. **Definition of Done, per story:** the failing test comes first, derived from the acceptance
   criteria; then minimal code; then edge and negative cases. Done only when the AC passes, tests
   are green, **the day-one gate is still green**, and a handover is written.
2. **Never fake, skip, `xfail`, comment out or delete a test to reach green. Never weaken an
   invariant to pass a check.** A red gate **blocks** — mark it `Blocked` with a note and surface it.
3. **Acceptance criteria MUST be binary.** "The dashboard works" is not acceptance criteria.
4. **The day-one proof is never waivable.** Empty database migrates → two users seeded → app starts
   → real browser login → user A reads their own row → **user B denied at the database layer** →
   the summary rule returns `75810`. Watched by a named human (`SW-ADR-009`, `SW-ADR-010`).
5. **Clean-clone evidence is a four-line ladder, never one tick** (`SW-ADR-009`). A check may be
   substituted in the open; it may not be quietly redefined.
6. Waiving any quality check is **reserved to the client**. Adopting a *stricter* option is not a
   waiver and needs no signature — that is why `SW-ADR-018` could be ruled by the build session.

## Article X — Open Decisions Register (explicitly NOT legislated here)

Listed as open. Deliberately not decided.

| ID | Question | Class | Owner |
|---|---|---|---|
| `OPEN-NAME-01` | The client's exact full name for the ratification block, and a backup decider (`NONE — accepted` is valid). **Until this lands, this Constitution is UNADOPTED and all 22 ADRs carry a "recorded while ungoverned" caveat.** | reserved: governance | client |
| `OPEN-MODEL-01` | What code and data may enter an AI model, and which vendors become sub-processors once real user data exists. | reserved: legal | client |
| `OPEN-CREDS-01` | Where database credentials live locally. `SW-ADR-014` replaced Secrets Manager with SSM for AWS; local development still needs an answer. Proposed: a git-ignored `.env` with `.env.example` committed. | reserved: secrets | client |
| `OPEN-SESSION-01` | Token lifetime and absolute session cap. `SRC-001 §5` defines neither. Proposed: 30-day absolute, 14-day idle for users, 30-minute idle for admins, id rotated on privilege change. | reversible | client |
| `OPEN-TZ-01` | Whose calendar resolves "this month". Proposed: the browser sends explicit `from`/`to` dates and the server never guesses. | reversible | build session |
| `OPEN-RATE-01` | `slowapi` stores rate limits in-process, so the limit is effectively multiplied by workers × tasks. A shared limiter needs a billable service, which `SW-ADR-014` forbids. Accepted knowingly, recorded not fixed. | (build-session ruled) | build session |
| `OPEN-DELETE-01` | Deleting a user orphans their receipt objects in S3. | reversible | build session |
| `OPEN-UNCAT-01` | The category breakdown needs an "Uncategorised" bucket for null `category_id`. Not in `SRC-001`. | reversible | build session |
| `OPEN-DEACT-01` | Does deactivating a user revoke their sessions? Not stated in `SRC-001`. Proposed: yes. | reversible | build session |

**No timeout defaults past a reserved matter.** If the approver is unavailable, that work stops.

## Article XI — Repository Reading Rules

1. **For decision status, trust the ledger. For document versions, trust the files on disk. For
   paths, trust the repo tree** — never a path quoted in prose.
2. `docs/` holds the delivery document set, numbered in dependency order. `00` is frozen input;
   `01` is the decision record; `02`→`06` is the derivation chain; `07`→`13` is proof and audit;
   `14`+ is lifecycle.
3. The root files are the working canon: `CLAUDE.md` (what a session reads first), `GOTCHAS.md`
   (the trap ledger), `PROGRESS.md` (the session log), `COORDINATION.md` (the lane map),
   `handoffs/` (what `/tt` writes and `/ss` reads back), `goals/` (the unit of work).
4. **`/ss` at the start of every session; `/tt` at the end of every session.** A session that ends
   without `/tt` has lost its memory.

## Article XII — Amendment & Ratification

1. Amending this Constitution is itself a **reserved matter.** A model may propose; only the named
   human adopts.
2. Amendments land as a superseding ADR plus a version bump here — never as a silent edit.
3. The version string `spendwise-constitution@0.1.0` is stamped on every governed decision. Use that
   exact string everywhere; two strings that drift by one word invalidate every record that carried
   the wrong one.

---

## Ratification block

```
STATUS:       DRAFT — UNADOPTED. Binds nobody until a named human signs below.
ADOPTED BY:   ____________________   (full name. "The team agreed" is not a name.)
ROLE:         ____________________
DATE:         ____________________
VERSION:      spendwise-constitution@0.1.0
SCOPE:        The SpendWise project only.
```

> **An unnamed signature is not a signature.** A name inferred from a git identity or an email
> address is not a signature either. If nobody will put their name here, that is important
> information about this project, and it should be said out loud now rather than in month four.
