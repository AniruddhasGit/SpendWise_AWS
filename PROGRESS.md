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
