# SpendWise — Claude Code Project Guide

> A personal expense tracker, built end to end from documents, by LLMs.
> **The build session writes application code AND builds AWS** (`SW-ADR-155`, superseding
> `SW-ADR-005` on 2026-09-13). Three environments are live; see `infra/README.md`.
>
> Gate: `CONSTITUTION.md` · Frozen sources: `docs/00 SourceOfTruth/` ·
> Decisions: `docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv` ·
> **Before committing: `py tools/consistency_check.py` (and `--selftest` before trusting a green).**

## Read at the start of EVERY session

1. **`GOTCHAS.md`** — the trap ledger. Before writing code, not after debugging.
2. **`PROGRESS.md`** — the last session block. What was done, what is half-done.
3. **`handoffs/`** — the newest `HANDOFF_<stamp>_<user>.md`. The previous session's own account.
4. **`bugs/README.md`** — **the mistake ledger, and your obligation to it.** 160 recorded defects
   in `BUG_LEDGER.md`, grouped by shape rather than by component, plus per-session write-ups in
   `bugs/sessions/` — 9 from the first deployment, 13 from building the pipeline. Two thirds are
   failures of *detection*, not of code: something was broken and nothing said so. Read
   `bugs/README.md` to understand the format, skim the shape that matches what you are about to
   touch, and **when you cause or find a bug, write it up there before you move on** — while you
   still remember what you wrongly believed. That field is the point of the whole folder and it is
   the first thing you forget.
5. **`COORDINATION.md`** — only if the DevOps session is running in parallel.

`/ss` does all four and reconciles them against git. **Start every session with `/ss`. End every
session with `/tt`.** A session that ends without `/tt` has lost its memory.

## Mission

A website where a person signs up, logs what they spend, and sees a dashboard of it.
**Everyone sees only their own money.** An admin role manages accounts — reset a password, force a
sign-out, deactivate — and **deliberately cannot see anyone's amounts or descriptions.**

Nothing here is novel. What matters is that it is built properly, deploys to AWS cleanly, and does
not turn into one giant file after two months.

## The document set — what to read for what

Numbered in dependency order. Each is derived from the ones above it and **cites them**.

| Folder | What it holds | State |
|---|---|---|
| `00 SourceOfTruth/` | `SRC-001` the client's requirements + `SRC-002` their rulings — **frozen and hashed**. **10 errata.** | **written** |
| `01 ADR/` | **155 decision records** (132 live, 23 superseded or withdrawn) + the fail-closed ledger. | **written** |
| `02 BRD/` | 76 business requirements, each citing a source. | **written** |
| `03 PRD/` | **42 specifications — the document the code is written from.** Plus the API contract and the §9 coverage map. | **written** |
| `05 Bible/` | 48 stories, **195 binary acceptance criteria**. The scope arbiter. | **written** |
| `05 B DesignSystem/` | Tokens + real CSS. Every contrast figure computed, not claimed. | **written** |
| `06 DataModel/` | A **package**: `datamodel.json` (spec of record) → generated `schema.sql`, `security.sql`, `TRACEABILITY.tsv`, plus `AGENT_CONTRACT.md` and runnable invariant checks. | **written** |
| `07 Architecture/` | `for_llm/` 8 docs, 11 diagrams · `for_humans/` overview, decisions owed, **the accepted weaknesses**. | **written** |
| `08 SIT/` · `09 NegativeTesting/` | **195 positive cases** (one per acceptance criterion) + 80 negative, **29 cross-person, 56 severity one**. | **written** |
| `10 EngineeringLedger/` | Derived from the Bible. **`/ss` reads this for the frontier** — verified: the hook finds it and prints the milestone matrix. Only `Status` is hand-edited. | **written** |
| `11 Journeys/` | Two personas, 16 walks, each naming the seam it crosses. | **written** |
| `12 DesignReview/` | The consolidated exit gate + the uncoached slice. | in progress |
| `14`–`40` | Lifecycle. `30 Deployment` holds the client's AWS prep queue. | placeholders |

**Authority on conflict** (`CONSTITUTION.md` Art II.1): raw `SRC-001` → a client ruling → an
`APPROVED` ADR → PRD → BRD → Bible → everything else. **Stricter always wins.**

## Stack — locked by `SW-ADR-016`. Do not substitute, even for something better.

**Backend** Python 3.12 · FastAPI + uvicorn · SQLAlchemy 2.0 async + asyncpg · Alembic ·
Pydantic v2 · PyJWT · bcrypt · boto3
**Frontend** React 18 + Vite · plain CSS · no UI framework
**Tests** pytest · pytest-asyncio · httpx (ASGITransport) · Playwright for the browser-observed
gate (`CV-16`) — locked on the same terms; do not substitute
**Data** PostgreSQL on AWS RDS · S3 for receipt images only
**Deploy** one image → ECR → **ECS on EC2** (free tier) · **no ALB · no Fargate · no NAT** ·
SSM Parameter Store (`SW-ADR-014`)

One container serves the API and the built React files; a catch-all route returns `index.html`.
One image, one service, one deploy, **no CORS** (`SW-ADR-020`).

## The shape

```
app/modules/{auth,users,expenses,categories,receipts,admin}/
    router.py · service.py · repository.py · schemas.py · models.py
app/core/       settings, db session, security, dependencies, errors
app/main.py     builds the app, includes every router
alembic/  ·  client/
```

Routers never write queries. Repositories never know what HTTP is. The service translates
(`SRC-001 §3.3`).

**A module touches only its own tables** (`SRC-001 §3.4`). The one sanctioned crossing
(`SW-ADR-017`): the expenses *repository* returns `category_id` + totals; the expenses *service*
asks the categories service for names. One round trip for the browser — which is what was asked
for. It asked for one request, not one SQL statement.

The shared folder is `core`, never `platform` — that name shadows a stdlib module.

## Non-negotiable invariants — enforce in CODE, never via a prompt

- **Isolation twice** (`SW-ADR-082`, `SW-ADR-078`): every query filters on the user id from the verified token,
  **and** Postgres RLS enforces it at the database with `FORCE ROW LEVEL SECURITY` on.
  A controller-only check is the classic false green.
- **The runtime DB role does not own the tables, is not superuser, holds no `BYPASSRLS`.**
  Verified by querying the catalog, never assumed. And **red-proofed** — the policy is disabled on
  purpose, the denial watched going red, reverted, and the revert verified.
- **Integer paise. Never a float.** `Decimal` at the boundary, `int` in a Pydantic validator,
  display string in React at render time only.
- **Cast `SUM()` to `BigInteger`** — Postgres returns a bigint sum as `numeric`.
- Cookie **httpOnly, SameSite=Lax**; `Secure` env-driven (`SW-ADR-014` left the deployment without
  TLS — a recorded weakness, never a default to copy).
- **bcrypt cost 12, off the event loop**; compare even for unknown emails.
- **Every admin action writes to the audit log in the same transaction as the change.**
- Password reset: hashed, single-use, one-hour, **and every session of that user revoked in the
  same transaction.**
- SQLAlchemy expression language. **No f-strings near SQL.**
- One `AsyncSession` per request via a dependency. **Never a module-level session.**

## Roles

Two, on a column: `user` and `admin`. `get_current_user` and `require_admin` written once, applied
as `dependencies=[Depends(require_admin)]` on the whole admin router — one place, never per handler.

First account claims admin **only if it matches `BOOTSTRAP_ADMIN_EMAIL`** (`SW-ADR-021`). An admin
cannot demote themselves if they are the last one.

**Admins never see amounts or descriptions.** Counts and dates only (`CONSTITUTION.md` Art VI.1).

## Status law — the rule that matters most

| Status | Meaning |
|---|---|
| `RULED` | decided, with a citation |
| `PROVISIONAL` | written down, a ruling outstanding |
| `OPEN` | genuinely unruled — **escalate, never invent** |
| `ASSUMED` | inference; never hardens into a constraint |

An agent that hits `OPEN` and fills in something sensible has committed the cardinal sin of this
project. Open items live in `CONSTITUTION.md` Article X.

**All 38 were adjudicated by Fable 5 on 2026-08-05** (`SW-ADR-091`…`128`), so no behaviour is
unruled. **Two remain client-only** and gate nothing: the ratification signature
(`OPEN-NAME-01`) and legal sub-processor posture (`OPEN-MODEL-01`), both with working defaults.
**Four rulings are flagged for the client's digest** and one message reverses any of them:
`OPEN-TZ-01` (irreversible on the write path), `OPEN-USERSRLS-01` (a quality-check waiver),
`OPEN-PRUNE-01` (deletes rows), `OPEN-CAT-01` (product content).

## Reserved — no model decides these, at any confidence

Money · anything irreversible or public · secrets · legal and data protection · amending
`CONSTITUTION.md` · what the product is and what "done" means · scope changes · **waiving any
quality check** · anything marked `[HUMAN]`.

No timeout defaults past these. Adopting a *stricter* option is **not** a waiver and needs no
signature — that is why the isolation rule could be ruled by the build session (`SW-ADR-078`,
superseding `SW-ADR-018`).

Under `SW-ADR-015` the build session decides technical questions and logs each as one
`[JUDGMENT CALL]` line; reversible reserved matters are decided then **batched** for the client to
reverse; reserved-and-irreversible still stops and waits.

## Honesty floor (`CONSTITUTION.md` Art VII)

**No invented evidence** — unverified means writing the word unverified · **worst number first**,
every rate carries its count · **a gap stays a gap** · **respect one-way doors** · **the log is the
memory** · **scope as written** · **the writer never verifies its own work** — where no second human
exists the substitute is a fresh zero-context session, and the substitution is recorded.

## Definition of Done

Failing test first, from the acceptance criteria. Then minimal code. Then edge and negative cases.
Done only when the AC passes, tests are green, **the day-one gate is still green**, and a handover
is written.

**Never fake, skip, `xfail`, comment out or delete a test to reach green.** A red gate blocks —
mark it `Blocked` with a note and surface it.

## The day-one proof — never waivable

Empty database migrates → **two** users seeded → app starts → real browser login → user A reads
their own row → **user B denied at the database layer** → the summary returns exactly **`75810`**
paise against the seeded fixture (`SW-ADR-010`). Watched by a named human. Then the RLS policy is
disabled on purpose and the denial is watched going red.

## Environment & secrets

Real values in `.env` (gitignored); `.env.example` committed. Typed `BaseSettings` that **fails
fast** — a missing required key aborts startup rather than defaulting silently. A missing key makes
the dependent story `Blocked`, never stubbed. **Never commit a credential**; `/tt` scans the staged
diff before every push.

## The build session builds AWS too

`SW-ADR-155` (2026-09-13, CLIENT) **supersedes `SW-ADR-005`**, which ruled that this session writes
application code only and creates nothing in AWS. That rule reflected the client's intention to
build DEV, UAT and PROD by hand in order to learn the DevOps role. It was reversed out loud, under
time pressure, and the reversal is recorded rather than assumed.

**Other documents still describe the old arrangement.** `CONSTITUTION.md`, `COORDINATION.md`, the
BRD, the PRD, the architecture notes and the deployment folder all carry `SW-ADR-005`'s framing,
each now marked as superseded at the point of citation. Where they disagree with this section, this
section is current. Rewriting their surrounding prose is outstanding editorial work, not a decision.

### What exists

Three environments on one EC2 host — `:8000` production, `:8001` uat, `:8002` dev — one RDS
instance with a database and its own login per environment, and a promotion pipeline. Start at
`infra/README.md`. The promotion rule is enforced in ECR, not GitHub, and has been watched refusing
a release.

### The RISK clause is discharged and reversed

`SW-ADR-005` warned this session would never observe AWS, so every AWS claim was *reasoned, not
observed*. That is no longer true and the superseding record discharges it: this session observes
AWS directly now, which raises the bar rather than lowering it: **an AWS
claim that was not observed is a defect**, not an accepted limitation. Art VII is unchanged — *here
is the command and here is the output*, never *the pipeline went green*.

### Still reserved, and not softened by any of this

Billing · anything that changes what the product is · waiving **or narrowing** a quality check ·
exposing a database to the public internet. Narrowing `tools/consistency_check.py` to exempt
fingerprinted sources was itself a reserved decision, taken by the client on 2026-09-13, not by a
session that found the gate inconvenient.

## Win condition — define victory, then stop

Sign up, log an expense, see a correct dashboard; a second person cannot see the first's money,
proven at the database layer; an admin can reset a password and force a sign-out; it runs on AWS
from a container the client deployed by hand.

Past that line is fast-follow: CSV import, the web manifest, note autocomplete, the expense-edit
screen, per-category budgets.

## Out of scope — do not build

No native mobile app · no reading bank SMS · no Account Aggregator or bank API · nothing pulled from
Google Pay or Blinkit · **no self-service password reset** (`SW-ADR-012` — there is no email in the
stack, so the token would have nowhere to go).
