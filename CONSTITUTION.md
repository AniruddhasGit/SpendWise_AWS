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

1. **The functional envelope is `docs/00 SourceOfTruth/SRC-001` plus the ADR records in
   `docs/01 ADR/all-ADRs/` as governed by the ledger.** No user-facing functionality beyond
   those two locations. The ledger held **144** records on 2026-08-05; per Art XI.1 **the
   ledger, never this sentence, is the count of record** — stated as a location rather than a
   number so this clause cannot go stale again.
   *(Counts refreshed 2026-08-05 per `SW-ADR-133`; the rule is unchanged.)*
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
3. **Errata govern over the text they correct.** They are enumerated in `SRC-001 §E`
   (`E-1`…`E-10` as of 2026-08-05), each citing the ADR that ruled it.
   *(Counts refreshed 2026-08-05 per `SW-ADR-133`; the rule is unchanged.)*
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
   cell to `INCLUDED` only with the carrying section cited in `notes`. **The derivation
   documents `02`–`11` now exist and are populated**, and the cells are derived from the
   citations actually present in each. The ledger is live state, not a snapshot: read it,
   never this sentence.
   *(Counts refreshed 2026-08-05 per `SW-ADR-133`; the rule is unchanged.)*
4. **Credentials MUST NEVER appear in an ADR, the ledger, or any committed file.**
5. **Status law**, applied to every schema, API and specification artifact:

   | Status | Meaning |
   |---|---|
   | `RULED` | decided, with a citation to `SRC-001` or an `APPROVED` ADR |
   | `PROVISIONAL` | written down, a ruling still outstanding |
   | `OPEN` | genuinely unruled — **escalate, never invent** |
   | `ASSUMED` | inference; never hardens into a constraint |

## Article IV — Security & Isolation Floors

1. **Per-user isolation is enforced twice** (`SW-ADR-078`, `SW-ADR-082` — superseding `SW-ADR-018`): every query filters on the user id from
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
   nothing created in AWS (`SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13)). The client builds DEV, UAT and PROD by hand.
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
   waiver and needs no signature — that is why the isolation rule could be ruled by the build session (`SW-ADR-078`, superseding `SW-ADR-018`).

## Article X — Open Decisions Register (explicitly NOT legislated here)

Listed as open. Deliberately not decided. **No timeout defaults past a reserved matter** — if the
approver is unavailable, that work stops.

Every row carries a class, an owner, and either a recommendation or an explicit statement that none
is offered and why. The client should be able to rule any row in under five minutes.

`GOAL_02`'s five-lens sweep found **127 undetermined decisions** across data shape, security, money
and time, user-visible behaviour, and operations. **48 were technical and are now ruled** as
`SW-ADR-023`…`SW-ADR-070` were ruled under `SW-ADR-015` (a historical range; several have since been superseded — for status read the ledger). The rest are below: they change what the product *is*,
they are irreversible, or they collide with a decision the client already made.

**Owner is the client on every row.** The build session raised them; it may not close them.

### X.1 — Blocking, in order of what they hold up

| ID | Question | Class | Recommendation |
|---|---|---|---|
| `OPEN-NAME-01` | **RULED — see `SW-ADR-091`.**  The client's exact full name for the ratification block, and a backup decider (`NONE — accepted` is valid). **Until this lands this Constitution is UNADOPTED and all 70 ADRs carry a "recorded while ungoverned" caveat.** | reserved: governance | — |
| `OPEN-CAT-01` | **RULED — see `SW-ADR-092`.**  **Which eight categories are seeded on account creation, and what colour each gets.** `SRC-001 §6.5` says "eight sensible ones" and names none. Inventing them is the build session inventing product content, which Art VII.3 forbids. Not cosmetic: they drive the ribbon, the breakdown and the day-one fixture, and changing the list later does not retro-fit existing accounts. | reserved: product identity | None offered — this is content, and content is the client's. It is also a one-message question. |
| `OPEN-MIGRATE-01` | **RULED — see `SW-ADR-093`.**  **Two APPROVED ADRs contradict each other.** `SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13) says migrations are "a separate runnable step, **never done on boot**". `SW-ADR-019` says "migrations remain at container start". Art II.1's authority order cannot separate two same-rank APPROVED records. | reserved: amending a ruling | None offered. The build session may not choose which of the client's own decisions loses. A superseding ADR is required either way. |
| `OPEN-CREDS-01` | **RULED — see `SW-ADR-094`.**  Where local database credentials live. `SW-ADR-014` replaced Secrets Manager with SSM for AWS; local development still needs an answer. | reserved: secrets | Git-ignored `.env`, with `.env.example` committed (`SW-ADR-060`). |
| `OPEN-MODEL-01` | **RULED — see `SW-ADR-095`.**  What code and data may enter an AI model, and which vendors become sub-processors once real user data exists. | reserved: legal | — |

### X.2 — Security and access

| ID | Question | Class | Recommendation |
|---|---|---|---|
| `OPEN-TZ-01` | **RULED — see `SW-ADR-096`.**  **Which calendar does this application run on?** `SW-ADR-010` caps the daily-average denominator "at today", which the *server* evaluates — and no timezone is named. On a UTC server an IST user's first 5.5 hours of every day still count as yesterday, so the headline average jumps 20-25% overnight; on the 1st of a month the denominator can reach zero. `SW-ADR-025` ruled Asia/Kolkata and **stated in its own text that it is IRREVERSIBLE on the write path** — the submission instant is never stored, so rows misfiled across a day boundary can never be identified afterwards. It was then ruled under the technical delegation anyway. **The QA was right that the build session should not have taken it.** Superseded by `SW-ADR-089`. | **IRREVERSIBLE** | Asia/Kolkata, named in settings; the server computes "today" in it; `spent_on` is never defaulted server-side. Downstream may proceed with it marked `PROVISIONAL`. |
| `OPEN-USERSRLS-01` | **RULED — see `SW-ADR-097`.**  **May the `users` table sit outside row-level security?** Login must read a user row by email *before* any verified user id exists, so a policy keyed on the request GUC can never serve it — and `SRC-001 §10.5`'s timing defence needs that lookup to return empty rather than error. `SW-ADR-042` therefore removed RLS from `users` and said so plainly: "the one table holding every email and password hash is outside the database-layer guarantee. That is a real reduction in the `SW-ADR-018` promise." **That is waiving a quality check, which Art IX.6 reserves to the client** — the same article that explains why `SW-ADR-018` could be ruled by the build session, because adopting the *stricter* option is not a waiver. `SW-ADR-071` shows the same root cause reached `password_resets` too. | **reserved: waiving a quality check** | Two real options: (a) `users` and `password_resets` outside RLS, application-layer only, as `SW-ADR-042`/`SW-ADR-071` argue; (b) a separate pre-auth database role holding `SELECT`/`INSERT` on those two tables only — stricter, costs a third credential and a second connection pool. |
| `OPEN-ADMINSELF-01` | **RULED — see `SW-ADR-098`.**  **May an admin act on their own row, or on another admin?** `SRC-001 §4.4` guards only self-*demotion* by the last admin — the identical lockout is reachable through `toggle is_active`, with no route back (`SW-ADR-012` removed self-service reset, `SW-ADR-021` rejected CLI seeding, `BOOTSTRAP_ADMIN_EMAIL` only covers a *fresh* database). Recovery would be hand-written SQL. Separately: admin-on-admin password reset is a complete takeover of a peer — the token is shown to the issuer and the target's sessions are revoked in the same transaction. | **IRREVERSIBLE** | Extend the last-admin guard to every action that would reach zero active admins — that follows §4.4's own logic. Whether one admin may take over another's account is the client's call. |
| `OPEN-SESSION-01` | **RULED — see `SW-ADR-099`.**  Token lifetime, absolute cap and idle expiry. `SRC-001 §5` defines none, and `sessions` has no `expires_at` column to hold one. With no `exp` claim the token is eternal — on a deployment running plain HTTP (`SW-ADR-014`). | reserved: product | 30-day absolute, 14-day idle for users, 30-minute idle for admins, id rotated on privilege change. Needs an `expires_at` column. |
| `OPEN-DEACT-01` | **RULED — see `SW-ADR-100`.**  The **complete** effect of `is_active = false`: refuse login, revoke live sessions, reject mid-session — and what the user is told. Deactivation is the admin's only containment tool; as specified it may be a flag that only affects a login form. | reserved: product | All three enforcement points. Generic 401 at login; an explicit message mid-session, where identity is already proven. |
| `OPEN-ROLECHG-01` | **RULED — see `SW-ADR-101`.**  What happens to live sessions when an admin changes a user's role, and whether the role is a token claim or re-read per request. A demoted admin otherwise keeps every admin power until the token expires — and `OPEN-SESSION-01` may leave that unbounded. | reserved: product | Re-read the role from the database; revoke sessions on demotion only. Makes the security-critical direction instant. |
| `OPEN-ENUM-01` | **RULED — see `SW-ADR-102`.**  **Does registration reveal that an email already exists?** `SRC-001 §10.5` spends real effort hiding this on the login path — running bcrypt against a dummy hash so timing reveals nothing — and the obvious registration implementation gives it away in plain text. | reserved: product | None offered. With no email anywhere in the stack (`SW-ADR-012`), a non-enumerable signup is genuinely user-hostile. That is a product judgement, not a code decision. |
| `OPEN-PWPOLICY-01` | **RULED — see `SW-ADR-103`.**  Any password policy at all — minimum and maximum length. `SRC-001 §10.10` assigns validation to Pydantic and never states the constraint, so a one-character password is accepted, and bcrypt silently truncates at 72 bytes so two long passphrases sharing a prefix authenticate each other. | reserved: product | Minimum 12, maximum 72 bytes, no composition rules. Document the 72 as a bcrypt property so nobody "improves" it later. |
| `OPEN-LOCKOUT-01` | **RULED — see `SW-ADR-104`.**  Are failed logins recorded, and does an account lock? `SRC-001 §1` assumes the locked-out state exists — it is the stated reason the admin role exists — but nothing in the specification can produce it, and a sustained attack leaves **zero** forensic trace. | reserved: product | Record failures unconditionally (nearly free, closes the forensic hole). Whether to *lock* is the client's call — with no self-service reset, a lockout means every locked user needs a human. |
| `OPEN-AUDIT-01` | **RULED — see `SW-ADR-105`.**  What `admin_audit_log.details` may contain, and whether admin *reads* are logged. `SRC-001 §6.7` leaves it unconstrained; `§6.9` makes the rows permanent. A "reset issued" row capturing the token would undo `§10.7`'s hashing entirely, and a "what changed" blob could carry amounts, breaching `§4.5` through the log rather than the screen. | **IRREVERSIBLE** | A closed allowlist of action types, each with a declared shape carrying no token, no amount, no description — plus a read-audit row for the three admin endpoints that expose other users' data. |
| `OPEN-SESSFIELDS-01` | **RULED — see `SW-ADR-106`.**  Does the admin session list show other users' **IP addresses and user-agent strings**? `§4.5` is a prohibition naming only amounts and descriptions, so a literal reading permits them — producing a screen showing every user's approximate location and device, which is more personally revealing than much of what `§4.5` protects. | reserved: product | Show user, `issued_at` and `last_seen_at` only. Keep IP for forensics, never surface it. `§9.3` asks only for "last active and status". |
| `OPEN-USERDEL-01` | **RULED — see `SW-ADR-107`.**  **Does user deletion exist at all?** `SRC-001 §6.9` specifies the cascade in careful detail, but `§4.2`'s matrix grants no one the permission and `§7.6` exposes no endpoint. | **IRREVERSIBLE** | Not in v1. Keep the cascade as schema-level correctness, and stop implying a capability the API does not have. Deletion is a one-way door and `SW-ADR-015` reserves exactly this. |

### X.3 — Product behaviour

| ID | Question | Class | Recommendation |
|---|---|---|---|
| `OPEN-CHIPS-01` | **RULED — see `SW-ADR-108`.**  What calendar range each period chip means. Where does the week start? Does "this month" end today or at month-end? `SRC-001 §9.2` names four chips and defines none — and if "this month" ends today, `SW-ADR-010`'s worked example is **unreachable through the UI**, so the day-one gate's 75,810 could never be produced by a chip. | reserved: product | ISO Monday-start; full calendar period for this month and this year; whole previous month for last month. The only set consistent with `SW-ADR-010`. |
| `OPEN-RIBBON-01` | **RULED — see `SW-ADR-109`.**  Does clicking a ribbon band re-scope the headline total, count, average and day bars — or only the entry list? `§9.2` says only "filters the list below". The per-day subtotals live *inside* the list, so if the headline does not follow, the page shows a total that visibly disagrees with the sum printed directly beneath it. | reserved: product | None offered. Both are defensible; the PRD must pick one and enumerate exactly which numbers move. |
| `OPEN-RESETUI-01` | **RULED — see `SW-ADR-110`.**  **Where does the user type the reset token?** `SW-ADR-012` kept the "complete a password reset" endpoint but `§9.1`'s page list has no screen for it. Built literally, the locked-out user — the exact person the admin role exists for — receives a token and a dead end. | reserved: product | A third mode on the sign-in page. Whichever is chosen must also specify what an expired, used, or wrong token shows. |
| `OPEN-FUTURE-01` | **RULED — see `SW-ADR-111`.**  May `spent_on` be in the future, and how far into the past? A future-dated expense enters the average's numerator while `SW-ADR-053`'s denominator is capped at today, so one rent entry dated next week inflates the average until that date passes. A mistyped year is accepted silently and sits outside every chip range. | reserved: product | Allow within a documented window (today − 10 years … today + 1 year) as a CHECK constraint; keep the numerator whole so total ÷ elapsed always reconciles. |
| `OPEN-DECIMALS-01` | **RULED — see `SW-ADR-112`.**  What happens to an amount with more than two decimal places — reject, or round? The discarded digit is stored nowhere, so a later change of mind cannot reconstruct what the user typed. | reserved: product | Reject with 422, with the React input restricted to two decimals so rejection is never the user's first encounter with the rule. No rounding on the write path at all. |
| `OPEN-UNCAT-01` | **RULED — see `SW-ADR-131`**, which supersedes `SW-ADR-113` and restates it in full.**  Does uncategorised spend appear as a bucket in the breakdown? Null `category_id` rows are guaranteed, not exotic — deleting a category nulls it on every historical expense. If the stitch drops them, the breakdown sums to less than the total on the same screen. | reserved: product | A synthetic "Uncategorised" bucket, clickable, always last — so the total always equals the sum of its own breakdown. |
| `OPEN-RENAME-01` | **RULED — see `SW-ADR-114`.**  **May a category be renamed?** `SRC-001 §7.2` lists only list/create/delete — yet justifies its own delete behaviour with "I don't want to lose history because I renamed something", so the prose assumes a capability the endpoint list omits. Same defect shape as `OPEN-USERDEL-01`: a behaviour implied by the reasoning and absent from the surface. | reserved: scope | Allow rename; renaming never affects the spending recorded against the category. Confirm explicitly rather than letting the PRD decide it silently. |
| `OPEN-DESC-01` | **RULED — see `SW-ADR-115`.**  Is `expenses.description` required? May it be empty? | reserved: product | Optional, maximum 500 characters (`SW-ADR-115`). |
| `OPEN-USEREDIT-01` | **RULED — see `SW-ADR-116`.**  May a user change their own email, display name, or password? No endpoint in `§7.1` offers it, so as specified the answer is no — which means a user who wants to change their password must ask an admin. | reserved: scope | Confirm "no" for v1 explicitly, rather than leaving it an accident of the endpoint list. |
| `OPEN-A11Y-01` | **RULED — see `SW-ADR-117`.**  `§9.4` asks for visible focus and respected reduced-motion and defines neither, so neither is testable. Worse: **the category ribbon has no keyboard or screen-reader equivalent at all** — the app's primary filter control is mouse-only. | reserved: product | Name WCAG 2.1 AA; specify a focus ring at ≥3:1; define reduced-motion as "appears instantly"; make each band a real focusable control. The ribbon needs deciding **before** the design system is written. |
| `OPEN-RANGECAP-01` | **RULED — see `SW-ADR-118`.**  Is the custom date range bounded? `§7.4` returns one row per calendar day, so a 2020–2026 range returns ~2,400 rows and ~2,400 sub-pixel bars in a fixed-width container. | reserved: product | 422 on `from > to`; a documented maximum span; coarser buckets above it as fast-follow. |
| `OPEN-DESTRUCT-01` | **RULED — see `SW-ADR-119`.**  Are destructive actions confirmed, and is the blast radius shown? Deleting a category silently strips categorisation from every expense that used it, with no undo. | reserved: product | Confirm on every destructive action, naming the count: "Delete Groceries? 47 expenses will become uncategorised." |

### X.4 — Operations

| ID | Question | Class | Recommendation |
|---|---|---|---|
| `OPEN-DEPLOY-01` | **RULED — see `SW-ADR-120`.**  With one EC2 instance and a fixed host port, **two tasks cannot run at once** — so ECS's default deployment configuration deadlocks on the port. The client must set minimum-healthy to 0 and accept a hard downtime window on every deploy. Owed as advance notice under Art VIII.2 and not yet in the prep queue. *(Reasoned, not observed.)* | reserved: product | Expand-contract as a standing rule: a migration may only add; destructive changes wait one release. Then image rollback is always safe. |
| `OPEN-DOWNGRADE-01` | **RULED — see `SW-ADR-121`.**  Must every migration carry a working `downgrade()`, and may a downgrade destroy data? Proving up/down/up on an *empty* schema proves nothing about downgrading a populated column. | **IRREVERSIBLE** | Forward-only for anything destructive, with rollback being restore-from-backup, stated plainly. A `downgrade()` that has never run against data is decoration — which Art VII.1 forbids. |
| `OPEN-PRUNE-01` | **RULED — see `SW-ADR-122`.**  Are `sessions` and `password_resets` rows ever deleted? `sessions` gains a row per login and never loses one, on a 20 GB instance with autoscaling deliberately off. | **IRREVERSIBLE** (deleting data) | Opportunistic pruning at login; never prune the audit log (`SW-ADR-083` makes it immutable anyway). Deleting rows is reserved, so this needs a signature before it ships. |
| `OPEN-S3LIFE-01` | **RULED — see `SW-ADR-123`.**  What happens to S3 objects uploaded but never attached, and to receipts when an expense is deleted? The presigned design means the browser writes before the server knows the key exists, so any interrupted upload leaves an object nothing can ever enumerate. *(Supersedes `OPEN-DELETE-01`, which covered only the user-deletion path.)* | **IRREVERSIBLE** | A `staging/` prefix with a 1-day expiry lifecycle rule; attach moves the key to its permanent prefix. The expiry window is the client's to name. |
| `OPEN-RESTORE-01` | **RULED — see `SW-ADR-124`.**  What does restoring from backup actually involve? RDS point-in-time restore produces a **new instance with a new endpoint**, so it changes `DATABASE_URL` and needs a redeploy — and the free tier covers roughly one instance. S3 is not in the snapshot, so a restore resurrects `receipt_key` values pointing at objects that may since have been deleted. The prep queue promises a restore drill against a go-live checklist that does not exist. | **IRREVERSIBLE** | Write the procedure before it is needed. Restore is a one-way door executed under pressure. |
| `OPEN-ROTATE-01` | **RULED — see `SW-ADR-125`.**  Rotating `JWT_SECRET` signs every user out instantly with no overlap window, while their `sessions` rows keep `revoked_at IS NULL` forever — so the admin dashboard then reports active sessions that do not exist. | reserved: product | Document rotation as a deliberate mass-logout, and revoke all sessions as part of the procedure. Note it in the prep queue when SSM is created — that is when the client first has a rotate button. |
| `OPEN-LOGS-01` | **RULED — see `SW-ADR-126`.**  Where does container stdout go, and for how long? The prep queue has an *alarms* row but no CloudWatch **Logs** row — no log group, no driver, no retention, no execution-role permission. With the default driver, logs die with every task, so the record of a crash loop is destroyed by the restart that caused it. | reserved: money (retention) | Add a prep-queue row: `awslogs` driver, a named log group, an explicit retention. The retention figure is a cost decision and is the client's. |
| `OPEN-MONITOR-01` | **RULED — see `SW-ADR-127`.**  **How does anyone learn the app is down?** `SRC-001 §7.7` justified `/healthz` by "that's what the load balancer calls" — and `SW-ADR-014` removed the load balancer. `/healthz` now exists and *nothing calls it*. | reserved: product | An ECS task-definition health check plus a CloudWatch alarm on running-task count below 1. If the client declines both, "the client is the monitor" belongs here as an explicit acceptance, not as an unnoticed hole. |
| `OPEN-RATE-01` | **RULED — see `SW-ADR-128`.**  `slowapi` stores rate limits in-process, so the effective limit is multiplied by workers × tasks. A shared limiter needs a billable service, which `SW-ADR-014` forbids. **Accepted knowingly; recorded, not fixed.** Separately, `SRC-001 §10.9` states the requirement only qualitatively — no threshold, no window, no key. | reserved: product | Dual key (per-IP and per-account), numbers divided by the worker count so the *effective* limit is the stated one. Whatever is chosen must be **numbers** — this cannot ship as prose, or no acceptance criterion here can be binary. |

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
