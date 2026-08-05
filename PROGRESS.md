# PROGRESS.md — append-only session log

> One block per session, so any session — any machine, any Claude account — resumes cold.
> Written by `/tt` at close. Newest at the bottom.
>
> **Narration describes intent. Git, the ledger and the gates describe reality.** When they
> disagree, that gap is the most valuable thing in this file — never smooth it over.

---

## 2026-08-05 · Session 1 · Foundations

**Done:**
- Repo initialised and pushed to `github.com/AniruddhaDynpro/SpendWise` (private).
  `.gitattributes` set to `* text=auto eol=lf`.
- **`/ss` + `/tt` installed and verified end to end** — commands in `.claude/commands/` (tracked,
  so any clone gets them) and user-global; `SessionStart` hook at
  `~/.claude/hooks/ss-autocontext.js`; wiring in the gitignored `.claude/settings.local.json`.
  Proven, not assumed: a handoff was written, then the hook was run and observed reading its
  *In progress*, *Next ready steps* and *Blockers* back.
- **`docs/` built as the numbered delivery set** — `00 SourceOfTruth` through `40 AMS`,
  in dependency order.
- **`SRC-001` frozen** — the client's requirements verbatim, clause-numbered so everything
  downstream cites `§n`, SHA-256 recorded in `fingerprints.json`, with **seven errata** appended
  where later rulings corrected it.
- **22 ADRs written** with a 20-column fail-closed ledger carrying the four `included_in_*`
  incorporation columns. All 22 read `NOT_INCLUDED` — correct, the derived documents do not exist.
- `CONSTITUTION.md` drafted — 12 articles, each citing where its rule came from.
- Root canon written: `CLAUDE.md`, `GOTCHAS.md`, `COORDINATION.md`, `goals/`.

**Rulings** (worst first — the ones that weaken something come before the ones that help):
- `SW-ADR-001` One person is client, money-signer and rules-signer. **This weakens the method's
  central control** — the decision queue never forms when the decider is also at the keyboard.
  Compensating control: a fresh zero-context second opinion on every irreversible call.
- `SW-ADR-014` **No Fargate, no ALB, no NAT, no Secrets Manager.** This *overrides the client's own
  written stack*, which specified Fargate behind a load balancer. Leaves a real hole: no TLS in the
  deployed environment, so the session cookie runs without `Secure` there.
- `SW-ADR-005` The build session touches no AWS. **It will therefore never observe the app running
  there** — every AWS claim it makes is reasoned, not observed.
- `SW-ADR-008` RDS from day one, overturning the build session's local-first recommendation.
- `SW-ADR-018` Isolation enforced twice — application filter **and** Postgres RLS with two database
  roles. Ruled by the build session: adopting the stricter option is not a waiver.
- `SW-ADR-010` The day-one rule — daily average = total ÷ days elapsed, capped at today.
  Agreed acceptance value **75,810 paise**.

**Corrections made to the client's own requirements** (`SRC-001` errata `E-1`…`E-7`): Alembic takes
no advisory lock; `slowapi` behind a proxy rate-limits the proxy; bcrypt at cost 12 blocks the event
loop; the first-admin claim was open to whoever found a fresh deployment first; self-service password
reset had no delivery route; currency could silently reinterpret history.

**In progress:** nothing half-finished. **No application code exists and none should yet** — the
derivation chain reaches code at `06 DataModel`, not before.

**Open / next:** `02 BRD` — business requirements, every line citing `SRC-001 §n`. Then `03 PRD`,
which is the document the code is actually written from.

**Blockers:**
- **`OPEN-NAME-01`** — the client's exact full name for the `CONSTITUTION.md` ratification block,
  plus a backup decider (`NONE — accepted` is a valid written answer). Until it lands the
  Constitution is **UNADOPTED** and all 22 ADRs carry a "recorded while ungoverned" caveat.
- **`OPEN-CREDS-01`** — where local database credentials live. Reserved: secrets. Blocks the first
  RDS connection.
- **`OPEN-MODEL-01`** — what may enter a model. Reserved: legal.
- Client-side AWS: `docs/30 Deployment/AWS_PREP_QUEUE.md` items 0–5.

**State:** no code · no schema · no AWS resource · **no check has been run on this project,
therefore none has been red-proofed, therefore no green here should be trusted by anyone including
its author.**

**Note on this repo's history:** rewritten on 2026-08-05 to a single root commit. The first
scaffolding pass used a different delivery method's document shapes; it was replaced wholesale by
the numbered set above rather than left half-converted in the history.

---

## 2026-08-05 · Session 1 (cont.) · GOAL_01 — freeze the client rulings

**Done:**
- **`SRC-002_client_rulings_2026-08-05.md` written and frozen** — 17 clauses covering every
  ruling the client made in this session, plus the framing statements and the standing
  delegation instruction that `SW-ADR-015` rests on entirely.
- **All 13 dangling citations closed.** Every ADR that cited *"Client statement, 2026-08-05"*
  — a reference that resolved to nothing on disk — now cites a real `SRC-002 §n` clause.
- `fingerprints.json` regenerated over both sources. **`SRC-001` verified byte-unchanged**
  against its recorded hash.
- Ledger `last_updated` + `notes` stamped on the 13 affected rows.

**Verified, not asserted** — checker output pasted in the handoff:
```
CITATIONS FOUND: 84 across 48 files
UNRESOLVED     : 0
'Client statement, 2026-08-05' still present in docs/01 ADR : 0 file(s)
FINGERPRINTS   : both match a fresh recomputation
SRC-001        : unchanged (19bc8eb7…812b71)
VERDICT: PASS
```

**Deviation from the goal, declared:** `GOAL_01` specified two provenance tags,
`[VERBATIM]` and `[PARAPHRASE]`. A third was added — **`[SELECTED]`**, for the seven rulings
that arrived through a multiple-choice interface where the build session authored the option
text. Forcing those into either existing tag would have been inaccurate in a way that
matters: it would either credit the client with words they did not write, or downgrade a
decision they definitively made. Declared in `SRC-002`'s reading rules.

**Finding carried forward, NOT fixed here:** 49 citations across 12 ADRs are written
`SRC-001 S11.5` (ASCII `S`) rather than `§11.5`. **They resolve** — nothing dangles — so this
is cosmetic, not the defect this goal targeted. Fixing them is **outside `GOAL_01`'s
write-set** (`Sources row ONLY`), so it was carried rather than silently widened into.
`GOAL_02` runs the same checker and should close it.

**In progress:** nothing half-finished.

**Open / next:** `GOAL_02_adr-completion.txt` — sweep `SRC-001`'s 66 sub-clauses for every
decision the BRD and PRD will need; rule what is rulable; raise the rest as `OPEN` rows.
Promote the throwaway citation checker into the repo so later goals reuse it, and close the
49 ASCII-`S` citations while in there.

**Blockers:** unchanged — `OPEN-NAME-01`, `OPEN-CREDS-01`, `OPEN-MODEL-01`, and
`docs/30 Deployment/AWS_PREP_QUEUE.md` items 0–5.

---

## 2026-08-05 · Session 1 (cont.) · GOAL_02 — ADR completion sweep

**Done:**
- Five fresh zero-context agents swept `SRC-001`'s 66 sub-clauses through distinct lenses —
  data shape (43 gaps), security (24), money and time (14), UX and error paths (25),
  operations (21). **127 undetermined decisions found.**
- **48 ruled** as `SW-ADR-023`…`SW-ADR-070` under `SW-ADR-015`. **35 OPEN rows** written into
  `CONSTITUTION.md` Article X, each with a class, an owner and a recommendation.
- Ledger extended to 70 rows. Citation checker re-run: 218 citations across 97 files,
  0 unresolved.

**Four findings that broke gates we thought were solid:**
- Date range semantics were undefined. Half-open would return **94,762 instead of the agreed
  75,810** — the never-waivable day-one gate was **not deterministic**.
- No timezone was named, so "capped at today" was wrong for 5.5 hours of every day on a UTC server.
- RLS as specified covered reads only.
- Foreign-key checks bypass RLS entirely, so a cross-user read was reachable through the category
  write path.
- `SW-ADR-005` and `SW-ADR-019` **directly contradict each other** on whether migrations run at
  boot. Raised as `OPEN-MIGRATE-01`, not resolved — the build session may not pick which of the
  client's own decisions loses.

**THEN THE FRESH-AGENT QA RAN, AND GOAL_02 DID NOT PASS IT. 24 findings, 3 CRITICAL.**

Worst first, because several are the build session's own errors:

- **CRITICAL — reset is uncompletable.** `SW-ADR-041` put `password_resets` behind RLS keyed on the
  verified user id. Completing a reset is *unauthenticated by definition* — the user is locked out,
  which is the whole reason the admin role exists. The policy matches nothing, so account recovery
  is dead. `SW-ADR-042` spotted this exact class of problem for `users` and fixed it only there.
- **CRITICAL — authority breach.** `SW-ADR-025` states in its own consequences that it is
  IRREVERSIBLE, and was then ruled by the build session anyway. `SW-ADR-015` says no delegation
  reaches irreversible matters. The one record that recognised the floor applied is the record that
  crossed it.
- **CRITICAL — the composite FK cannot work as written.** `ON DELETE SET NULL` on a composite key
  nulls **every** referencing column including `user_id`, which is `NOT NULL`. The column-list form
  needs PostgreSQL 15, and **no document pins a version** — the prep queue literally asks the client
  which one they will create.
- **HIGH — two more contradictions** the sweep missed: `SW-ADR-064` vs `SW-ADR-070` on where the
  build version lives; `SW-ADR-030` vs `SW-ADR-043` on whether admin can read expense counts at all.
- **HIGH — a second waiver ruled without a signature.** `SW-ADR-042` removes the database-layer
  guarantee from the table holding every password hash, and says so in its own text. That is
  waiving a quality check, which is reserved to the client.
- **HIGH — two claimed actions that never happened.** `SW-ADR-069` says "Filed as ERRATUM E-8" and
  there is no E-8. `SW-ADR-029` says "erratum candidate" and filed none. Four ADRs claim prep-queue
  rows that do not exist. **That is a K1 breach by the build session** — reporting an action as
  done when it was not.
- **HIGH — `SW-ADR-024` is wrong.** "All timestamps NOT NULL" makes `revoked_at` and `used_at`
  unsatisfiable, and `SW-ADR-039` indexes `revoked_at IS NULL` — an index over a condition its own
  sibling ADR makes impossible. The stated count of eleven columns is also wrong; there are ten.
- **HIGH — `SW-ADR-059` silently closed a reserved question** by putting `/reset` in the route map,
  which is `OPEN-RESETUI-01`, and answered it differently from the register's own recommendation.

**Factually wrong premises the QA corrected** (the decisions mostly survive; the reasoning did not):
`SW-ADR-041`'s justification is wrong — a `FOR ALL … USING` policy *does* constrain writes, and a
`FOR SELECT`-only policy fails loud rather than leaking · `SW-ADR-036` — `sum(bigint)` returns
`numeric` and cannot overflow; the risk is the mandated cast back · `SW-ADR-045` — PyJWT 2.x
*requires* `algorithms`, so an unpinned decode is a startup error, not a bypass (the real missing
control is a version floor) · `SW-ADR-052`'s worked example is muddled · `SET LOCAL` cannot take a
bind parameter, so the RLS mechanism as written forces the f-string-near-SQL that Art IV.8 forbids.

**In progress:** GOAL_02 is **NOT closed.** 24 findings are unadjudicated.

**Open / next:** remediate before `GOAL_03`. Superseding ADRs for the three CRITICALs and the
contradictions; move `SW-ADR-025` and `SW-ADR-042` to OPEN rows; actually file the errata that were
claimed; add the four missing prep-queue rows; correct the wrong premises. The BRD must not be
written on top of this.

**Blockers:** unchanged, plus `OPEN-MIGRATE-01`.

---

## 2026-08-05 · Session 1 (cont.) · GOAL_02 remediation

**All 24 QA findings adjudicated.** 20 superseding ADRs written (`SW-ADR-071`…`SW-ADR-090`),
3 errata filed, 4 prep-queue rows added, 2 rulings withdrawn.

**The two I should not have made, handed back:**
- `SW-ADR-025` (application timezone) → **withdrawn** by `SW-ADR-089`. It stated in its own text
  that it was IRREVERSIBLE and was ruled under the technical delegation anyway. Now `OPEN-TZ-01`.
- `SW-ADR-042` (`users` outside RLS) → **withdrawn** by `SW-ADR-090`. It waived a quality check,
  which Art IX.6 reserves to the client. Now `OPEN-USERSRLS-01`, with the stricter alternative
  the original never offered.

**The three CRITICALs:**
- `SW-ADR-071` — password reset was **uncompletable**. RLS keyed on a verified user id cannot
  serve a path that is unauthenticated by definition. `password_resets` leaves RLS, with the
  root cause named once rather than patched twice.
- `SW-ADR-072` — the composite FK could not work: `ON DELETE SET NULL` nulls *every* referencing
  column including `NOT NULL user_id`. Now `NO ACTION` plus an explicit service-side update, with
  no PostgreSQL version floor required.
- `SW-ADR-089` — above.

**Three more contradictions, resolved:** `SW-ADR-073` (version endpoint), `SW-ADR-077` (admin
expense counts), `SW-ADR-076` (timestamp nullability — "all NOT NULL" made `revoked_at IS NULL`
unsatisfiable while a sibling ADR indexed exactly that condition).

**Wrong premises corrected, decisions kept:** `SW-ADR-078` (RLS write behaviour — a `FOR ALL …
USING` policy *does* constrain writes; a `FOR SELECT`-only policy fails loud, not silent),
`SW-ADR-079` (`sum(bigint)` returns `numeric` and cannot overflow — the risk is the mandated
cast), `SW-ADR-080` (PyJWT 2.x already requires `algorithms`; the real missing control was a
version floor), `SW-ADR-085` (a muddled worked example in the ADR that makes the gate
deterministic).

**Two design collapses the sweep missed and the QA caught:** `SW-ADR-081` — `FORCE ROW LEVEL
SECURITY` subjects the *owner* to policies, so data migrations would silently affect zero rows;
`SW-ADR-082` — `SET LOCAL` cannot take a bind parameter, so the stated RLS mechanism forced the
f-string-near-SQL that Art IV.8 forbids. Both were reachable through the design's own text.

**Verified:**
```
consistency_check.py            VERDICT: PASS — every cross-reference resolves   (exit 0)
consistency_check.py --selftest 7/7 checks observed firing on a planted violation
ledger rows: 90 · ADR files: 90 · errata: E-1..E-10 · frozen sources fingerprinted: 2
```

**`SRC-001` hash changed** when E-8/E-9/E-10 were appended. Adjudicated in writing inside
`fingerprints.json` rather than left as a silent bump: errata are additive, and the derived
artifacts affected are exactly the three ADRs that filed them.

**Residual the mechanical layer cannot see:** `SW-ADR-070`'s body cites "`SW-ADR-071`'s
prep-queue row". `SW-ADR-071` now exists — but it is about password resets, not a prep-queue
row. The reference *resolves* and is *semantically wrong*. `SW-ADR-070` is superseded by
`SW-ADR-073` and carries a banner, so the reader is directed correctly. This is a live example
of exactly why `GOAL_13`'s agent layer exists: a checker that only asks "does it resolve?"
cannot ask "does it mean the right thing?"

**In progress:** nothing half-finished. **GOAL_02 is now closed.**

**Open / next:** `GOAL_03` — the BRD. Two Article X rows are newly the client's and gate nothing
technically: `OPEN-TZ-01`, `OPEN-USERSRLS-01`.

**Blockers:** `OPEN-NAME-01` · `OPEN-CREDS-01` · `OPEN-MODEL-01` · `OPEN-CAT-01` (the eight seeded
categories — a one-message question that blocks the day-one fixture) · `OPEN-MIGRATE-01` (two of
the client's own APPROVED ADRs contradict each other) · AWS prep queue items 0–9.

---

## 2026-08-05 · Session 1 (cont.) · GOAL_03 — the BRD

**v0.1 written, reviewed, and it failed.** 28 findings from a fresh zero-context reviewer,
3 CRITICAL. Repaired as v0.2.

**The three criticals — all mine:**
- **The BRD cited two WITHDRAWN ADRs as live authority** for `N-ISO-01`, the product's central
  security promise. `SW-ADR-018` and `SW-ADR-041` were both superseded during the `GOAL_02`
  remediation *earlier in this same session*. A PRD written from `SW-ADR-041` would have put
  `password_resets` behind RLS and **broken account recovery** — the exact critical bug
  `SW-ADR-071` was written to fix, reintroduced one document later.
- **`N-ISO-01` asserted an absolute guarantee that is false.** Two tables sit outside the
  database layer deliberately, and whether that is acceptable is `OPEN-USERSRLS-01` — reserved
  to the client. The BRD stated the settled version and made the carve-outs invisible.
- **§6 closed two reserved OPEN rows**, one marked IRREVERSIBLE, by listing them as scope
  exclusions and citing the open rows themselves as the authority. The document's own §1 says
  "escalate, never invent".

**The largest coverage hole:** `SRC-001 §9.4` had **zero** representation — accessibility, phone
width, and the entire visual identity. Since `§12.1` excludes a native app, phone-width web *is*
the whole mobile product, and it had no requirement at all.

**Also caught:** the colophon's "nothing was invented" was false in six places · `R-UND-04`
quoted the superseded formulation of the daily-average rule and dropped both the null case and
half-up rounding, making the day-one `75810` unreproducible · §7 said two blockers where the
register lists five · `R-ADM-04`/`06` authorised complete admin-on-admin account takeover as
settled · the negative half of the permission matrix (what a non-admin *cannot* do) had no home ·
rate limiting and the locked-out state were both absent, the second being the sole justification
for the administrator persona · `N-MON-01` forbade the `Decimal` parsing that `SRC-001 §10.1`
mandates · the day-one proof was stated read-only when `SW-ADR-078` extended it to writes and
deletes.

**v0.2:** 77 requirement rows (up from 53), 31 OPEN, 3 PROVISIONAL. Scope corrected to the **70
live** records, not all 90. `OPEN-RENAME-01` raised — `SRC-001 §7.2` justifies its delete
behaviour with "I don't want to lose history because I renamed something" while listing no
rename endpoint. Same defect shape as `OPEN-USERDEL-01`.

**Verified:** `consistency_check` PASS · 21 ADRs flipped `included_in_brd` with the carrying row
cited, **live records only** · 2 stale flags cleared · no withdrawn record cited as authority
(the two matches are §2 naming them as examples of what is *out* of scope).

**What this says about the method:** the mechanical checker passed the BRD in both versions. It
resolves every reference in a document that cited withdrawn decisions as live authority — because
"does it resolve?" and "is it still true?" are different questions. `GOAL_13`'s agent layer is
the only thing that catches this, and it caught it here.

**In progress:** nothing half-finished. GOAL_03 closed.

**Open / next:** `GOAL_04` — the design system. `OPEN-A11Y-01` must be settled *before* it is
written, per the register's own note: the category ribbon is the primary filter control and has
no keyboard equivalent.

**Blockers:** `OPEN-NAME-01` · `OPEN-CAT-01` · `OPEN-MIGRATE-01` · `OPEN-CREDS-01` ·
`OPEN-MODEL-01` · AWS prep queue items 0–9.

---

## 2026-08-05 · Session 1 (cont.) · Escalation to Fable 5, and GOAL_04

**All 38 Article X rows escalated to Fable 5 and ruled** — `SW-ADR-091`…`SW-ADR-128`.
36 decided; 2 declined as genuinely client-only (a signature, and legal sub-processor posture)
with working defaults so nothing blocks.

**Four flagged for the client digest** — each formally crosses a line the register reserved,
ruled under the client's escalation grant and reversible by one message:
`OPEN-TZ-01` (irreversible on the write path — the veto window closes when the first real
expense row is written) · `OPEN-USERSRLS-01` (a quality-check waiver) · `OPEN-PRUNE-01`
(deletes rows) · `OPEN-CAT-01` (product content).

**`OPEN-MIGRATE-01` resolved for `SW-ADR-019`** — migrations run at container start. Fable's
reasoning: Art II.1 puts raw `SRC-001` above any ADR, and `§11.6` is the client's own hand
saying "at container start, before uvicorn binds the port". The losing sentence in
`SW-ADR-005` is a drafter's gloss inside a decision about *who writes what*, not about
migration timing — and against a hand-deployed single instance it is also the worse answer.

**GOAL_04 — the design system.** `DESIGN-SYSTEM.md` + `tokens.css`, 59 custom properties.

**Every contrast figure was computed, not asserted** — and one failed:

```
Uncategorised  #a8a29e   2.36:1   FAIL   (needs 3:1 — it is a UI component, not text)
               #948c87   3.09:1   ok     darkened within hue
```

`SW-ADR-092` had anticipated exactly this: *"MUST verify each at >=3:1 against the paper
surface, adjusting tone within hue if any fails."* The instruction was followed rather than
the number taken on trust. **A document that asserted compliance instead of computing it would
have shipped a band nobody could see.** All 11 text pairs and all 9 bands now pass.

`tokens.css` validated: braces balanced, 59 properties, **no raw hex outside the token block**
— so no component can reference a colour directly.

**The ribbon is now a real control** (`SW-ADR-118`): each band a native `<button>`, one Tab
stop with roving tabindex, arrow-key navigation, `aria-pressed`, and selection signalled by
**two** cues — an outline marker plus dimming — so it survives colour blindness. A sliver band
is still reachable by arrow key and still announces its full name, which is the keyboard
equivalent of a pointer target too small to hit.

**In progress:** GOAL_04 written and self-verified; its fresh-agent QA has not yet run.

**Open / next:** QA GOAL_04, then GOAL_05 (the PRD — the largest artifact in the project).

---

## 2026-08-05 · Session 2 · Goals 03–13, and the exit gate

**Done:**
- **Goals 03 → 13**, each executed, then QA'd by fresh zero-context agents, then repaired.
  `02 BRD` (76 requirements, re-derived to v0.3) · `03 PRD` (42 specifications + a **generated**
  API contract) · `05 Bible` (48 stories, 195 binary criteria) · `05 B DesignSystem` ·
  `06 DataModel` (spec of record + 3 generated artifacts) · `07 Architecture` · `08 SIT`
  (195 cases, one per criterion) · `09 NegativeTesting` (80 cases, 29 cross-person, 56 SEV-1) ·
  `10 EngineeringLedger` · `11 Journeys` · `12 DesignReview`.
- **`01 ADR` grew 22 → 144 records** (123 live, 21 superseded or withdrawn).
- **A live isolation hole found and closed.** `security.sql` carried an unqualified permissive RLS
  policy on `expenses`; a row-level policy has no column dimension and permissive policies are
  OR'd, so it returned every column of every row to any connection with `app.is_admin` set.
  `SRC-001 §4.5` was false at the database while the PRD claimed it was structurally true, and
  **no stated test could have caught it**. `SW-ADR-129`.
- **`tools/consistency_check.py` grew 9 → 15 checks**, each added because the previous set passed
  while a real defect walked through it. **15/15 red-proofed.** 8 generated artifacts verified by
  regeneration. 8/8 seams two-way covered.

**Not done — recorded as a failure, not smoothed over:**
- **GOAL_13's Definition of Done was zero guesses from a fresh uncoached engineer. Never reached.**
  Seven runs: **18 → 21 → 15 → 8 → 8 → 8 → 7**. In five of the seven, at least one finding was a
  defect introduced by the previous round's repair. Full data:
  `docs/12 DesignReview/EX_Consolidated-Exit-Gate/05_UNCOACHED_SLICE_LOG.md`.
- **No application code exists.** No database has been created. The day-one proof has never run.
  Everything in this repo is a claim about documents, checked against other documents.

**In progress:** nothing half-finished.

**Open / next:** **M0 — the day-one spine.** Failing test first; finish line is the never-waivable
gate returning exactly `75810` paise with person B denied at the database layer, then the RLS
policy disabled on purpose and the denial watched going red.

- **Session closed 2026-08-05_1907 by ani87** → handoff: handoffs/HANDOFF_2026-08-05_1907_ani87.md

---

## Session 2026-08-06 — the application exists, and it runs

The previous block closed with *"No application code exists. No database has been created. The
day-one proof has never run."* All three are now false.

**Built:** M0 (the day-one spine), M2 (the API), M3 (the client), M4 (the admin module), the
E0-S10 endpoints, and a shell rebuild — sidebar, light/dark/system, glass, a line plot, a donut
that is also a filter, custom categories, settings, an administration console.

**`CR-001`:** the client reversed two frozen requirements — no user deletion (`SW-ADR-107`) and
an administrator who may not see amounts (`SRC-001 §4.2`). Recorded as a change request with
superseding records, because `SRC-001` is fingerprinted and cannot be struck where it stands.
Deletion is SOFT; the administrator sees *how much over time* and still not *what on*, held by a
three-column return type rather than by a response model.

**418 tests pass** (50 in Chromium) in one clean sequential run. `consistency_check` PASS with
16/16 red-proofed, 12 generated artifacts verified by regeneration, every contrast pair measured
in both themes.

**Four defects that passed review and were caught only by running the thing** — `SW-ADR-146` (the
gate read the wall clock and went red at midnight), `SW-ADR-147` (a contrast pair at 2.36:1, the
same hex already fixed under a different token), `SW-ADR-149` (three admin capabilities that
returned a plausible answer and did nothing, because `FORCE ROW LEVEL SECURITY` applies to the
owner too), and a false green in a test that asserted a privacy boundary against a pane which had
rendered nothing.

**Not done, recorded as such:** no rate limiting exists — every auth endpoint is unthrottled
(`E1-S6`). M5 receipts is Blocked on an S3 bucket. `E0-S10`'s fresh-clone run signed by a named
human has not happened. Nothing is deployed.

**A cost worth recording:** the `CR-001` work was built by four agents in parallel sharing one
`spendwise_test`. Per-test `TRUNCATE` landed mid-seed in other processes and produced a real
Postgres `DeadlockDetectedError`; no agent could get a clean full run. Do not parallelise pytest
against this database again without a per-worker database or a lock.

**In progress:** nothing half-finished.

**Open / next:** rate limits (`E1-S6`), then M6 hardening — the log deny-list red-proofed
(`E6-S1`) and the capabilities that must not exist (`E6-S5`).

- **Session closed 2026-08-06_0442 by ani87** → handoff: handoffs/HANDOFF_2026-08-06_0442_ani87.md
