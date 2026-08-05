# AWS_PREP_QUEUE.md — the client's advance-notice queue

**Owner: the client.** Everything here is built by hand, in the AWS console, deliberately, to
practise the DevOps role (`SW-ADR-005`). The build session creates nothing in AWS and writes no
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
| Master username | anything except `admin`, `root`, `postgres` | RDS reserves some names and rejects them at the *end* of the wizard |

**Report back:** endpoint, port, Postgres major version, master username. **Not the password.**

**Standing constraint.** The free tier covers roughly **750 instance-hours/month** against ~730 hours
in a month — that is **one** instance. DEV + UAT + PROD as three live instances is roughly 3× over.
Options when you get there: one instance with three databases inside it; stop instances when idle
(RDS stops for up to 7 days, storage still bills, instance-hours don't); or accept the cost. Decide
before building the second one.

### 3. Two database roles — **load-bearing for the day-one gate** (`SW-ADR-018`)

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

These were promised by an ADR and never written down. That is the obligation `SW-ADR-005`
trades for the code-only boundary, so the lapse is recorded rather than quietly corrected.

### 6. A CORS rule on the S3 bucket  (`SW-ADR-069`, `SRC-001` erratum E-8)

`SRC-001 §2.4` says there is no CORS to configure. **That is wrong for receipts.** The browser
uploads straight to S3, which is a second origin. Without this rule every upload fails with an
opaque browser error and no response body the app can read.

Allow `PUT` and `POST` from the application's origin, with the headers the presigned policy
signs, and `ETag` exposed. **Needed by:** the first receipt upload (`GOAL_08` onwards).

### 7. Both SSM parameters as `SecureString`  (`SW-ADR-045`)

`DATABASE_URL` and `JWT_SECRET`. A plain `String` parameter is **unencrypted**, is returned to
anything holding broad SSM read permission, and — unlike `SecureString` — needs no KMS grant, so
the least-effort choice is the insecure one. `SecureString` additionally needs `kms:Decrypt` on
the **execution** role for the key you choose. **Needed by:** the first deploy.

### 8. A second database in the same RDS instance  (`SW-ADR-068`)

`spendwise_dev` and `spendwise_test`, with the same two roles in each. The day-one proof drops
and rebuilds the schema from empty — run against a single database that destroys whatever you
were working with. Costs nothing extra; it is two `CREATE DATABASE` statements.
**Needed by:** the first test run, which is before any application code.

### 9. An ECS task-definition health check  (`SW-ADR-070`, `OPEN-MONITOR-01`)

`SRC-001 §7.7` justified `/healthz` by "that's what the load balancer calls" — and `SW-ADR-014`
removed the load balancer. **`/healthz` currently exists and nothing calls it.** Point the task
definition's health check at it so ECS itself restarts an unhealthy task.
**Needed by:** the first deploy. See also `OPEN-LOGS-01` — there is still no CloudWatch Logs row.

---

## How this file works

- The build session adds items **before** it needs them, with a "needed by", and says so in chat at
  the same time.
- **Nothing here is created by the build session.** If something in this list appears in AWS that
  you did not create, that is a defect — report it.
- When you finish an item, **say what you actually created.** Under `CONSTITUTION.md` Art VII.1 the
  build session cannot write "the RDS instance exists" because it is on this list — only because
  you said it does.
