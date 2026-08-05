# SpendWise

A personal expense tracker. One deployable — a modular monolith with six
modules and hard internal boundaries — serving both the API and the built
React client from a single origin (`SW-ADR-020`), so there is no CORS and the
session cookie is first-party.

Sign up, log what you spend, see a correct dashboard. A second person cannot
see the first's money, and that is proved at the database layer, not asserted.

![The dashboard](evidence/screens/02-dashboard-person-a.png)

---

## Running it

### 1. Configuration

Everything lives in `.env`, which is **gitignored and has never been
committed**. Copy the manifest and fill it in:

```
cp .env.example .env
```

The application refuses to start with a missing required key — it exits **78**
naming every one of them, before uvicorn binds the port. That is deliberate
(`E0-S1` AC3): a process that boots and then fails on the first request has
already told a load balancer it is healthy.

### 2. The database

RDS PostgreSQL 18, `ap-south-1`, two databases in the one instance
(`SW-ADR-068`): `spendwise` and `spendwise_test`. Two roles:

| role | what it does |
|---|---|
| `spendwise_owner` | owns every table, runs Alembic, **never serves a request** |
| `spendwise_app` | serves every request, holds no DDL, subject to row-level security |

Migrations run under `MIGRATION_DATABASE_URL`; the application runs under
`DATABASE_URL`, and a boot assertion fails closed if they are the same string.

```
py -m alembic upgrade head
```

### 3. The client

```
cd client
npm install
npm run build
```

`client/dist` is what the API serves. Without it the API still runs and logs
one warning — the backend does not depend on the frontend toolchain.

### 4. Start

```
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000>.

For frontend work, `npm run dev` in `client/` proxies `/api` to port 8000, so
the development setup keeps the single-origin shape production has.

---

## Checking it

```
py -m pytest                        # 322 tests, ~3.5 min against real RDS
py -m pytest -m "not db"            # the pure ones, no network
py -m pytest -m gate                # the never-waivable day-one proof
py -m pytest tests/browser          # 28 Chromium tests against a real server

py tools/consistency_check.py       # every cross-reference in the documents
py tools/consistency_check.py --selftest   # 16/16 checks proved to fire
py client/sync_tokens.py --check    # the client's design tokens have not drifted
cd client && npm run lint:tokens    # no raw hex, one money formatter, one focus rule
```

**The gate** (`CONSTITUTION` Art IX.4) is `daily_average_paise == 75810` over
the seeded day-one fixture. It is computed by application code from rows
PostgreSQL returned under row-level security, read back through the real
endpoint, and — since `GOAL_14` — also read off the screen in a real browser.

It is evaluated as of **2026-08-05** and every runner pins
`APP_TODAY_OVERRIDE` to that date. The divisor is days elapsed, so the value
changes every midnight; `SW-ADR-146` records the day that was found the hard
way.

---

## What is here

| | |
|---|---|
| `app/` | the monolith. `core/` is shared; `modules/{auth,users,expenses,categories,receipts,admin}/` each own their tables |
| `client/` | React 18 + Vite, plain CSS, no UI framework. Tokens are **generated** from the design system |
| `alembic/` | one baseline migration, generated from `docs/06 DataModel/datamodel.json` |
| `tests/` | 322 tests. `tests/browser/` drives Chromium against a real uvicorn |
| `tools/` | `consistency_check.py`, and the scripts that produce evidence |
| `docs/` | 146 decision records, the frozen source, the PRD, the data model, the design system — see `docs/README.md` |

Nine artifacts are **generated** and verified by regeneration on every run of
`consistency_check.py`: the schema, the policies, the traceability matrix, the
bootstrap script, the baseline migration, the API contract's rendered pages,
the expected summary fixture, `docs/README.md`, and the client's design tokens.
Editing one by hand is erased by the next run, silently — so none of them are
edited by hand.

---

## What is not built

Recorded rather than implied by a green suite:

| | |
|---|---|
| **M5 receipts** | needs an S3 bucket that does not exist. `S3_BUCKET` stays unset, `receipts_enabled` reports `false`, the client hides the control, and one WARN names the disabled feature at boot. Designed behaviour — but a gap in coverage |
| **M4 admin** | the six admin stories |
| **M6 hardening** | rate limits, password reset endpoints |
| **E0-S10** | the endpoints exist and are tested; the fresh-clone run signed by a named human has not happened |

`docs/10 EngineeringLedger/engineering_ledger.tsv` is the frontier. Anything
not built is `Backlog` or `InProgress` with the reason — never quietly `Done`.
