# HANDOFF — 2026-08-25_1715

| | |
|---|---|
| **When** | Tuesday 25 August 2026, 17:15 IST |
| **Developer** | Aniruddha Jathar |
| **Repo** | `D:/SpendWise` |
| **Branch** | `main` |
| **Latest commit** | `86ec53b` — *chore(handoff): close-out 2026-08-25_1556* |
| **Lane** | **OPS** — CI and AWS. No application code was written. |

---

## In progress — READ FIRST

**No code is half-finished.** `app/`, `client/`, `alembic/` and `tests/` are byte-identical to
`2026-08-21_1605`. No story was opened, no migration authored, no test touched.

### ⚠️ One action is outstanding and it is security, not housekeeping

> **The AWS access key used this session was pasted into a chat window. Rotate it.**
>
> The IAM user `AWS_cli_dynpro` holds **`AdministratorAccess`** — full control of account
> `944483082287`, including IAM and billing. Its key reached a transcript, so treat it as public.
>
> ```
> IAM → Users → AWS_cli_dynpro → Security credentials → Access keys → Deactivate → Delete
> aws configure --profile spendwise      # with the replacement, typed at the prompt
> ```
>
> Also delete, if still on disk: `CLI_access_key_claude.txt`, `Aniruddha_AWS_accessKeys.csv`,
> `Dyn_pro_laptop_IAM_User_credentials.csv`, `~/Downloads/dyone_keys.txt`. None of them are inside
> `D:/SpendWise`, so nothing is at risk of being committed — verified.
>
> Two earlier keys were also exposed and should be confirmed dead: `AKIA5XZ4…OQX5` and
> the console password for `Dyn_pro_laptop_IAM_User`.

---

## What this session did

### 1. RDS exists, and the day-one gate is green for the first time

The blocker carried by every handoff since `2026-08-05` is cleared.

| | |
|---|---|
| Endpoint | `spendwise-db.c9y6yemgc4pn.ap-south-1.rds.amazonaws.com:5432` |
| Engine | **PostgreSQL 17.9** |
| Class / storage | `db.t4g.micro` · 20 GB gp2 · **autoscaling off** |
| Region / AZ | `ap-south-1` (Mumbai) · `ap-south-1c` |
| Databases | `spendwise`, `spendwise_test` — both owned by `spendwise_owner` |
| Roles | `spendwise_owner`, `spendwise_app` |
| Security group | `sg-09febaad6c66d18cd` — TCP 5432 from `27.107.64.142/32` only |
| Master user | `swadmin` |

**Role attributes verified against `pg_roles`, not assumed** (`CONSTITUTION` Art IV.3):

```
     rolname     | rolsuper | rolbypassrls | rolcreaterole | rolcreatedb
-----------------+----------+--------------+---------------+-------------
 spendwise_app   |    f     |      f       |       f       |      f
 spendwise_owner |    f     |      f       |       f       |      f
```

**Then the suite ran against it:**

```
pytest -m "not browser"   →  418 passed, 0 failed, 0 skipped
pytest -m "gate"          →  12 passed
```

The 209 tests that had been skipping for want of a database now execute. **The `75810` day-one
proof passes against real RDS.** Note what is still *not* proven: the browser-observed half
(`CV-16`, Playwright) has not been run, and neither has the deliberate red-proof where the RLS
policy is disabled and the denial watched going red. **The gate is green; it is not yet
red-proofed.** That distinction is the whole point of the rule and should not be blurred.

### 2. Cost guardrails, before anything billable

`spendwise-monthly-cap` — $20/month, alerts at 50% actual, 80% actual, 100% **forecasted**, all to
`aniruddha.jathar@dynpro.com`. Deliberately $20 and not $100: the credits are a *total*, not a
monthly allowance, so a mistake takes months to matter and you hear about it in week one.
Console shows **$139.80 credits remaining**, more than the $100 assumed.

### 3. `.env` points at RDS

Both URLs rewritten, `?ssl=require` on each. `.env` confirmed still gitignored. A backup of the
previous `.env` is in the session scratchpad, not the repo.

**No third env file was created, despite being asked for.** `.env` (real, ignored) and
`.env.example` (manifest, committed) are both load-bearing — `app/core/settings.py` diffs them
against the `Settings` class in both directions, and a test enforces it. A third would be a second
source of truth for the same secrets.

### 4. Three real defects in `docs/30 Deployment/rds_bootstrap.sql`

The generated bootstrap **cannot run as written.** All three are `generate.py` fixes and belong to
the BUILD lane; none were touched this session.

1. **psql does not interpolate `:'vars'` inside `DO $$ … $$`.** Dollar-quoted strings are opaque to
   psql's variable substitution, so `PASSWORD :'spendwise_owner_password'` reaches the server
   literally and fails with `syntax error at or near ":"`. `CREATE ROLE` must be emitted *outside*
   the DO block.
2. **PostgreSQL 16+ requires `GRANT <owner> TO <creator>`** before `CREATE DATABASE … WITH OWNER`,
   or it fails with `must be able to SET ROLE`. The script has no such grant.
3. **The script and the prep queue disagree on the dev database name.** `rds_bootstrap.sql` says
   `spendwise`; `AWS_PREP_QUEUE.md` item 8 says `spendwise_dev`. **`spendwise` is correct** —
   `.env.example` and `conftest.py`'s `_swap_db` both key off that exact name. The prep queue is wrong.

Worked around by running the equivalent statements by hand. The workaround SQL is in the scratchpad,
not the repo, because the fix belongs in the generator.

### 5. CI — four jobs, self-documenting

Committed earlier in `a117bc7`. `assemble` · `image` · `tests` · `secrets`, each carrying a header
naming which catalogue family it covers, what green proves, and what green misses. Top of the file
holds a coverage map and an execution graph; the bottom holds a NOT-BUILT-YET block.

**Three CI failures were hit and diagnosed, each worth keeping:**

- **A duplicate `image:` key.** PyYAML parsed it happily — duplicate keys are legal YAML, last one
  wins — and GitHub rejected the file outright: 0 seconds, no jobs, the run named after the file
  path because GitHub never reached `name:`. **A local parse is not a schema check.**
- **The container refused to boot, correctly.** `alembic/env.py` raised on
  `MIGRATION_DATABASE_URL == DATABASE_URL` (`SW-ADR-081`) — the workflow had handed the postgres
  service's one superuser to both. The application enforced its own invariant against the pipeline.
- **Docker Hub returned a 500** pulling `node:20-alpine`. Not ours — a non-hermetic dependency.

**A `concurrency` lesson, learned the hard way:** `cancel-in-progress: true` cancelled the very
re-run being waited on, twice, because a later push landed on the same ref. Consider scoping it so
`main` always runs to completion:

```yaml
cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

### 6. `docs/aws/rds.html` — an ELI18 explainer

Six short sections: why a database at all, what was created and why, the two-roles decision, how it
wires into the code, what it unlocked, how to rebuild. Self-contained, light/dark aware, no external
assets. Written for understanding, not as a runbook.

### 7. `C:\Ideal\CI_DESIGN_PLAYBOOK.md` — written earlier today, outside the repo

Deliberately outside: it is project-agnostic and reusable. Twelve sections including a catalogue of
seven check families whose seventh column is **"what green does NOT tell you"**. `ci.yml`'s comments
cite it by section number.

---

## Current state

- **Working tree** clean apart from `docs/aws/` (committed by this close-out).
- **Ledger unchanged** — M0 9/10 · M1 8/8 · M2 8/8 · M3 8/8 · M4 6/6 · M5 0/3 · M6 1/5. No Status
  was flipped because nothing was built. **The M6 rows are now genuinely unblocked**, which is a
  change in circumstance, not in the ledger.
- **CI**: `assemble`, `tests`, `secrets` observed green. `image` last observed **cancelled** by the
  concurrency rule, not failed. Its true state is unverified — the last clean signal on it was a
  Docker Hub 500.
- **Nothing deployed.** ECR, ECS and SSM remain untouched.

### Remotes

| Remote | Repo | State |
|---|---|---|
| `personal` | `AniruddhasGit/SpendWise` | current |
| `origin` | `AniruddhaDynpro/SpendWise` | **behind — push rejected** |

Git identity is `169955520+AniruddhasGit@users.noreply.github.com`, so `origin` returns
`Repository not found`. Sync it or retire it — a client call.

### AWS console access

`Dyn_pro_laptop_IAM_User` can sign in but holds only `IAMUserChangePassword` — every page reads
*Access Denied*. Attaching `ReadOnlyAccess` + `AmazonRDSFullAccess` was offered and **declined**;
the client will use root and the CLI. Recorded so the next session doesn't re-diagnose it.

**Region trap, hit once already:** the console opens on the last region used. `spendwise-db` is in
**Mumbai**. Viewing N. Virginia shows *0 DB instances*, which looks exactly like nothing was built.

---

## Next ready steps

1. **Rotate the access key.** Above. Before anything else.
2. **Red-proof the day-one gate.** Green is not the same as proven. Disable the RLS policy on
   purpose, watch the isolation test go red, revert, and verify the revert — with a named human
   observing. That plus the Playwright half closes `E0-S10` and makes **M0 10/10**.
3. **`E6-S1`** — the log deny-list. The M6 frontier, and it needed exactly the database that now
   exists. Its AC plants a reset code and a password through the real issue and sign-in paths and
   asserts neither reaches stdout.
4. **`E6-S2` … `E6-S4`** — chained behind `E6-S1`, all now unblocked.
5. **Fix `generate.py`** so `rds_bootstrap.sql` regenerates correctly — the three defects above —
   and correct `AWS_PREP_QUEUE.md` item 8's database name. BUILD lane.
6. **Two CI jobs that need nothing external:** `tools/consistency_check.py`, and `actionlint`
   (nothing currently checks `ci.yml` itself — defect #1 above is the argument for it).
7. **`E5-S3`** — graceful absence of the receipts bucket. Needs no S3 and no RDS.

---

## Blockers / decisions pending

| Blocker | Owner |
|---|---|
| **Rotate the exposed admin access key** | you — today |
| **S3 bucket** — `E5-S1` / `E5-S2` only | you (AWS) |
| **`E0-S10`'s named-human observation** — now the only thing between here and M0 10/10 | you |
| **`origin` unreachable under the current identity** — sync or retire | you |
| **Bible stories for six undocumented capabilities** — a scope decision | you |
| **`GET /api/admin/overview` has no authorising ADR** | you |

### A decision deliberately not taken

The CI Postgres service now has the same role separation as production, so RLS *could* bite there —
which makes it tempting to run the `db`-marked tests in CI and call isolation proven.
**Left alone.** `SW-ADR-008` rules that gate against real RDS and `GOTCHAS.md` names a stand-in
PostgreSQL as a false-green hazard for exactly it. That is an ADR-level decision, not a CI tweak.

---

## Resume protocol

1. `git pull` — `personal`, not `origin`.
2. Rotate the key if it is still alive. Nothing else matters until it is.
3. Read `CLAUDE.md` and `GOTCHAS.md`.
4. `docs/aws/rds.html` explains the database; `C:\Ideal\CI_DESIGN_PLAYBOOK.md` explains the CI file.
5. Confirm RDS is still reachable — the security group allows **one IP**, and home IPs move:
   ```
   aws rds describe-db-instances --db-instance-identifier spendwise-db --profile spendwise
   ```
   If the app cannot connect, check that rule before anything else.
6. `.github/workflows/**` is **OPS** territory under `COORDINATION.md`, claimed deliberately.
7. Then `E6-S1`.
