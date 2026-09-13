# AWS_PREP_QUEUE.md — the client's advance-notice queue

**Owner: the client.** Everything here is built by hand, in the AWS console, deliberately, to
practise the DevOps role (`SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13)). The build session creates nothing in AWS and writes no
pipeline or infrastructure code. Its job is to say what is coming **before** it is needed.

```
Last updated .... 2026-08-05
Blocking now .... items 0-4 — the day-one proof cannot run without them
Target .......... SW-ADR-014: ECS on EC2 · no load balancer · no NAT · SSM Parameter Store
```

> **Prices below are approximate and UNVERIFIED by the build session** (`CONSTITUTION.md` Art VII.1).
> They exist so nothing lands as a surprise, not so a budget can be built from them. Money is
> reserved to the client.

---

## NOW — before the day-one proof can run

### 0. A billing alarm. Genuinely before anything that costs money.

- **Billing → Budgets** → a monthly ceiling, alerts at 50% / 80% / 100%. Even $5 is fine — the point
  is the email.
- **Billing → Preferences** → free-tier usage alerts on.
- **Check which free-tier model this account is on.** AWS moved to a credit-based free tier for new
  signups in 2025; older accounts kept the 12-month model. The build session has **not checked and
  will not guess** — it changes what everything below costs.

**Why first:** an alarm set up afterwards only tells you about a bill you already ran up.

### 1. Stop using the root account

MFA on root, then put it away. Create an admin user for yourself, MFA on that too, work as that.
Not on the critical path — but doing it later means redoing every resource's ownership story, and
"who did this?" is a question this project's whole method cares about.

### 2. One RDS PostgreSQL instance — **this is the blocker** (`SW-ADR-008`)

| Setting | Value | Why |
|---|---|---|
| Engine | **PostgreSQL** | row-level security is what the day-one gate rests on |
| Version | newest major RDS offers — **tell me which** | migrations and code get pinned to it |
| Class | **db.t4g.micro** (or `t3.micro`) | cheapest free-tier-eligible |
| Storage | **20 GB gp SSD, autoscaling OFF** | 20 GB is the free-tier line; autoscaling silently crosses it |
| Multi-AZ | **No** | not free tier |
| Public access | **Yes** for now — see item 4 | the build session must reach it |
| Backups | **7 days** | a restore drill is on the go-live checklist |
| Deletion protection | **Off** while learning | you will want to delete and rebuild this |
| Credentials management | **Self managed** — NOT AWS Secrets Manager | Secrets Manager bills ~$0.40/secret/month where SSM Parameter Store is free. `SW-ADR-014` rejected it by name, and the RDS wizard warns about the charge on the page itself. |
| Create method | **Standard create**, not Easy create | Easy create hides public access, storage autoscaling, backups and deletion protection — three of which this table needs set differently from their defaults. Storage autoscaling in particular defaults **ON** and silently crosses the 20 GB free-tier line. |
| Master username | anything except `admin`, `root`, `postgres` — e.g. `swadmin` | **This instance is publicly reachable, and `postgres` is the first username anyone tries.** (An earlier version of this row said RDS *reserves* those names. For the PostgreSQL engine that is reliably true of `rdsadmin`, not of `postgres` — corrected 2026-08-05 rather than left as a plausible-sounding reason that is not the real one.) |

**Report back:** endpoint, port, Postgres major version, master username. **Not the password.**

**Standing constraint.** The free tier covers roughly **750 instance-hours/month** against ~730 hours
in a month — that is **one** instance. DEV + UAT + PROD as three live instances is roughly 3× over.
Options when you get there: one instance with three databases inside it; stop instances when idle
(RDS stops for up to 7 days, storage still bills, instance-hours don't); or accept the cost. Decide
before building the second one.

### 3. Two database roles — **load-bearing for the day-one gate** (`SW-ADR-082`)

Not one connection string. Two roles:

- **owner/migration role** — creates the schema, runs Alembic, owns the tables.
- **runtime role** — what the app connects as. **Does NOT own the tables, is NOT superuser, holds NO
  `BYPASSRLS`.**

Plus `FORCE ROW LEVEL SECURITY` on every protected table, because **a table's owner bypasses RLS
otherwise, silently.** The build session will supply the exact SQL as a migration; who runs it
depends on `OPEN-CREDS-01`.

**If this is skipped, the isolation gate passes for the wrong reason** — which is worse than failing.

### 4. Network access

- Security group inbound: **PostgreSQL / TCP 5432, source = your current IP only.** Not
  `0.0.0.0/0` — an open Postgres port is found in hours.
- Your home IP changes. When the app suddenly cannot connect, check this first.

A publicly-reachable RDS instance locked to one IP is normal for a dev database. It is **not** what
production looks like — that sits in a private subnet reachable only by the application. Worth
knowing now so the later change is deliberate rather than inherited.

### 5. `OPEN-CREDS-01` — where do local credentials live?

Reserved: secrets. The build session will not choose, and will never ask for a password in chat.
Proposed: a **git-ignored `.env`** locally with `.env.example` committed, and **SSM Parameter Store**
once ECS appears (free, and what the task definition will want). `.gitignore` already blocks `.env`,
so the ordering is safe.

Decide with it: does the client run the role-creation SQL, or does the build session run it from a
connection string? Either is fine — if the latter, that string is a credential and lives wherever
this rules.

---

## NOT YET — warnings, so nothing surprises you

| What | When it becomes real | What to know now |
|---|---|---|
| **ECR repository** | before the first image push | 500 MB free; images add up faster than expected |
| **EC2 instance for ECS** | before the first deploy | `t2`/`t3.micro`, 750 h/month free for 12 months. **1 GB RAM must host the ECS agent and your container together** — workable, tight |
| **ECS cluster + task definition** | before the first deploy | EC2 launch type, **not Fargate** (`SW-ADR-014`). Task publishes to a host port |
| **No load balancer** | — | Reached by the instance's public IP or an Elastic IP. **Therefore no TLS**, therefore `Secure=false` on the cookie in that environment, therefore **it is never called production** |
| **S3 bucket** | when receipts are built | Block all public access; per-user key prefix; 5-minute signed URLs. **Plus a CORS rule** — see item 6. |
| **SSM Parameter Store** | with the task definition | Free at Standard tier. **Both `DATABASE_URL` and `JWT_SECRET` must be `SecureString`, not `String`** — see item 7. Execution role reads parameters; task role reaches S3 (`SRC-001 §11.5`) |
| **CloudWatch alarms** | before anything is trusted | Every alarm must be **forced once** to prove it fires. An alarm nobody has watched fire is decoration |

**Deliberately not used, and why:** Fargate (no meaningful free tier) · Application Load Balancer
(~$16–18/month regardless of traffic) · NAT Gateway (~$32/month, larger than everything else
combined) · Secrets Manager (~$0.40/secret/month where SSM is free).

---

## ADDED 2026-08-05 — four items owed as advance notice, found by the GOAL_02 review

These were promised by an ADR and never written down. That is the obligation `SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13)
trades for the code-only boundary, so the lapse is recorded rather than quietly corrected.

### 6. A CORS rule on the S3 bucket  (`SW-ADR-069`, `SRC-001` erratum E-8)

`SRC-001 §2.4` says there is no CORS to configure. **That is wrong for receipts.** The browser
uploads straight to S3, which is a second origin. Without this rule every upload fails with an
opaque browser error and no response body the app can read.

Allow `PUT` and `POST` from the application's origin, with the headers the presigned policy
signs, and `ETag` exposed. **Needed by:** the first receipt upload (`GOAL_08` onwards).

### 7. **Three** SSM parameters, all as `SecureString`  (`SW-ADR-080`, `SW-ADR-081`)

`DATABASE_URL` and `JWT_SECRET`. A plain `String` parameter is **unencrypted**, is returned to
anything holding broad SSM read permission, and — unlike `SecureString` — needs no KMS grant, so
the least-effort choice is the insecure one. `SecureString` additionally needs `kms:Decrypt` on
the **execution** role for the key you choose. **Needed by:** the first deploy.

### 8. A second database in the same RDS instance  (`SW-ADR-068`)

`spendwise_dev` and `spendwise_test`, with the same two roles in each. The day-one proof drops
and rebuilds the schema from empty — run against a single database that destroys whatever you
were working with. Costs nothing extra; it is two `CREATE DATABASE` statements.
**Needed by:** the first test run, which is before any application code.

### 9. An ECS task-definition health check  (`SW-ADR-127`, `OPEN-MONITOR-01`)

`SRC-001 §7.7` justified `/healthz` by "that's what the load balancer calls" — and `SW-ADR-014`
removed the load balancer. **`/healthz` currently exists and nothing calls it.** Point the task
definition's health check at it so ECS itself restarts an unhealthy task.
**Needed by:** the first deploy. See also `OPEN-LOGS-01` — there is still no CloudWatch Logs row.

---

### 10. CloudWatch Logs  (`SW-ADR-126`, `OPEN-LOGS-01`)

**Owed and previously missing.** `SW-ADR-126` ruled this and the row was never written — caught by
the `GOAL_13` X-04 sweep, which checks every claimed action against the artifact it names.

- Create log group **`/ecs/spendwise`**, with **retention set at creation — default 30 days.**
- Wire the task definition to the **`awslogs`** driver targeting it. Turn **auto-create off**, so a
  misconfigured task fails loudly instead of quietly making a second group.
- Grant the **execution** role `logs:CreateLogStream` and `logs:PutLogEvents`.

**Needed by:** the first deploy. Before it, the default driver keeps logs on the instance — so a
crash loop destroys the record of the crash that caused it.

Retention is a cost dial and therefore yours; 30 days sits well inside the free allowance at this
volume. *(Approximate and unverified by the build session.)*

---

## ADDED 2026-08-05 (later) — four items owed, found by the GOAL_13 exit gate

`SW-ADR-127` asserted in its own text that **both** its items "are prep-queue rows". One was.
`SW-ADR-123` and `SW-ADR-120` were never queued at all. Art VIII.2 makes advance notice the
obligation traded for the code-only boundary, so an unqueued dependency is a broken promise,
not a small omission.

### 11. A CloudWatch alarm on the service running at all  (`SW-ADR-127`)

One alarm on the ECS service's `RunningTaskCount < 1` for **2 consecutive minutes**, notifying an
SNS topic with your email subscribed and **confirmed** (an unconfirmed subscription is silent).

**Needed by:** the first deploy. **Force it once** — stop the task by hand and check the mail
actually arrives. An alarm nobody has seen fire is an assumption, not a control.

The health check of item 9 restarts a container that has *stopped answering*. This alarm covers the
case it cannot: the container is gone and nothing is restarting it. There is no ALB, so nothing
else notices.

### 12. An S3 lifecycle rule expiring `staging/`  (`SW-ADR-123`)

One rule on the receipts bucket: **expire objects under the `staging/` prefix after 1 day.**

**Needed by:** the first receipt upload. An upload that is abandoned between the presigned POST and
the attach call leaves an orphan under `staging/`. `P-RCP-01` and `08_failure_modes.md` both promise
those "expire after one day" — a promise that rests entirely on this rule existing.

### 13. ECS deployment configuration: minimum-healthy **0**  (`SW-ADR-120`)

On the service: **minimum healthy percent 0, maximum percent 100.**

**Needed by:** the first *re*deploy — not the first deploy. One EC2 instance, one host port: the
new task cannot start until the old one stops. At the default minimum-healthy 100 ECS waits for a
healthy new task before stopping the old one, and the deploy **deadlocks silently** until it times
out. This costs one short outage per deploy, which is the correct trade at this size.

### 14. A third SSM parameter for the migration credential  (`SW-ADR-081`)

`MIGRATION_DATABASE_URL`, `SecureString`, alongside `DATABASE_URL` and `JWT_SECRET`.

**Needed by:** the first deploy — before it, not after. `P-OPS-02`'s boot sequence runs migrations
under the **owner** role and then serves traffic under the **runtime** role, and asserts at startup
that the runtime role owns no table. Two roles with different passwords are two connection strings.
The prep queue said "both parameters", which quietly assumed one.

---

## How this file works


- The build session adds items **before** it needs them, with a "needed by", and says so in chat at
  the same time.
- **Nothing here is created by the build session.** If something in this list appears in AWS that
  you did not create, that is a defect — report it.
- When you finish an item, **say what you actually created.** Under `CONSTITUTION.md` Art VII.1 the
  build session cannot write "the RDS instance exists" because it is on this list — only because
  you said it does.

---

## AS BUILT — recorded by OPS, 2026-08-25

`COORDINATION.md`'s handshake: OPS records **what actually exists**, observed, not what this queue
says should exist. Everything below was verified by querying it.

| Item | Status | What exists |
|---|---|---|
| 1. Billing alarm | ✅ | `spendwise-monthly-cap` — $20/mo, alerts at 50% / 80% actual and 100% forecasted |
| 2. RDS instance | ✅ | `spendwise-db.c9y6yemgc4pn.ap-south-1.rds.amazonaws.com:5432` · **PostgreSQL 17.9** · `db.t4g.micro` · 20 GB gp2, autoscaling **off** · `ap-south-1c` · master `swadmin` |
| 3. Two roles | ✅ | `spendwise_owner`, `spendwise_app` — both `NOSUPERUSER NOBYPASSRLS NOCREATEROLE NOCREATEDB`, verified against `pg_roles` |
| 4. Network access | ✅ | `sg-09febaad6c66d18cd` — TCP 5432, source `27.107.64.142/32` only |
| 6. S3 bucket | ☐ | not created — blocks `E5-S1`, `E5-S2` only |
| 7. SSM parameters | ☐ | not created — deploy-time, not needed for local work |
| 8. Second database | ✅ | `spendwise` and `spendwise_test`, both owned by `spendwise_owner` |

Account `944483082287`, region `ap-south-1`. Console credits remaining at time of build: **$139.80**.

**Version pinned for the record:** PostgreSQL **17.9**, not the newest RDS offered (18.6). Chosen
deliberately — nothing in this project needs an 18-only feature, and a first build wants the version
with the most production mileage behind it. `--no-auto-minor-version-upgrade` is set, so AWS will
not move it.

### Three defects in `rds_bootstrap.sql` — the script cannot run as generated

Found by running it. All three are `generate.py` fixes and belong to the BUILD lane.

1. **psql does not interpolate `:'vars'` inside `DO $$ … $$`.** Dollar-quoted strings are opaque to
   psql's variable substitution, so `PASSWORD :'spendwise_owner_password'` reaches the server
   literally: `ERROR: syntax error at or near ":"`. `CREATE ROLE` must be emitted outside the block.
2. **PostgreSQL 16+ requires `GRANT <owner> TO <creator>`** before `CREATE DATABASE … WITH OWNER`,
   else `ERROR: must be able to SET ROLE "spendwise_owner"`. No such grant is emitted.
3. **This file's item 8 names the dev database `spendwise_dev`; `rds_bootstrap.sql` names it
   `spendwise`.** `spendwise` is correct — `.env.example` and `conftest.py`'s `_swap_db` both key
   off that exact name. **Item 8 above is the error**, corrected here rather than left standing.

Worked around by hand this session so the build could proceed; the generator is still wrong.
