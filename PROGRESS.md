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
