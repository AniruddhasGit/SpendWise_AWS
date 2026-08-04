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
