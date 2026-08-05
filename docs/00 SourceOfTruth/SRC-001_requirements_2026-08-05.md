# SRC-001 — SpendWise requirements, as given by the client

```
Source type ....... Client requirements statement (written)
Received .......... 2026-08-05
Author ............ the client (SpendWise owner)
Status ............ FROZEN — never edited
Citation form ..... SRC-001 §n
```

> **FROZEN INPUT. DO NOT EDIT.** Every requirement in `02 BRD`, `03 PRD`, `05 Bible` and
> `06 DataModel` cites a clause of this file. If this file changes, everything derived from it is
> invalidated and must be re-derived — never silently reused (`CONSTITUTION.md` Art II.4).
>
> The **only** permitted modification is a clearly-marked `ERRATUM` block appended at the foot,
> which governs over the text it corrects. Ten errata now exist — see §E. They govern over the text they correct.
>
> Clause anchors `§n` were added when the text was filed. **No wording was changed.**

---

## §1 — What is being built

I want a website where people sign up, log what they spend, and see a dashboard of it. Everyone
sees only their own money. There's also an admin role that can manage accounts, because I need
someone to be able to reset a password when a user locks themselves out.

Nothing about this is novel. What I care about is that it's built properly, that it deploys to AWS
cleanly, and that the code doesn't turn into one giant file after two months.

## §2 — Stack

> "I've already decided these. Please don't substitute alternatives, even better ones."

**§2.1 Backend** — Python 3.12, FastAPI, running under uvicorn · SQLAlchemy 2.0 with the async
engine and asyncpg · Alembic for migrations · Pydantic v2 for request and response models · PyJWT
for tokens, `bcrypt` for password hashing · boto3 for S3.

**§2.2 Frontend** — React 18 with Vite, plain CSS, no UI framework.

**§2.3 Infrastructure** — PostgreSQL on AWS RDS · S3 for receipt images, nothing else · Docker
image, pushed to ECR, running on ECS Fargate behind a load balancer.
*(Superseded in part — see ERRATUM E-1.)*

**§2.4 Topology** — One container serves both the built React files and the API. FastAPI mounts the
Vite build with `StaticFiles` and a catch-all route returns `index.html` so client-side routing
works. I don't want a separate CloudFront distribution for the frontend. One image, one repo, one
service, one deploy command, and no CORS to configure because the browser only ever talks to one
origin.

## §3 — Modular monolith

**§3.1** It ships as one container. Internally it's split into modules that don't reach into each
other.

```
app/
  modules/
    auth/         registration, login, sessions, password reset
    users/        profiles, roles
    expenses/     the actual thing the app does
    categories/
    receipts/     S3 signed URLs
    admin/        everything that needs the admin role
  core/           settings, db session, security, dependencies, errors
  main.py         builds the FastAPI app, includes every router
alembic/
client/           the React app
```

**§3.2** Every module gets the same five files: `router.py` for the endpoints, `service.py` for the
logic, `repository.py` for the queries, `schemas.py` for the Pydantic models, `models.py` for the
SQLAlchemy tables.

**§3.3** Routers never write queries. Repositories never know what HTTP is. Routers deal in Pydantic
schemas, repositories deal in SQLAlchemy models, and the service in the middle translates.

**§3.4** The rule I actually care about: **a module only touches its own tables.** If `admin` needs
expense counts, it calls the expenses service, it does not `select(Expense)` itself. This is the
whole point. If I ever want to pull expenses out into its own service, the seam is already there and
I'm not chasing queries through six files.

**§3.5** Call the shared folder `core`, not `platform`. `platform` is a Python standard library
module and a top-level package with that name will shadow it. `core` holds infrastructure only — no
business logic lives there.

## §4 — Roles

**§4.1** Two of them, `user` and `admin`, stored as a column on the users table. Not a separate
permissions table — I don't need that much flexibility and it would just be one more join.

**§4.2** The permission matrix:

| | user | admin |
|---|---|---|
| Own expenses and categories | yes | yes |
| See anyone else's expense amounts | no | **no** (see §4.5) |
| List all accounts | no | yes |
| See who is currently signed in | no | yes |
| Force sign someone out | no | yes |
| Issue a password reset | no | yes |
| Deactivate or reactivate an account | no | yes |
| Promote or demote an admin | no | yes |
| Read the admin audit log | no | yes |

**§4.3** This is what FastAPI's dependency system is for. Write `get_current_user` once and
`require_admin` once, then put `dependencies=[Depends(require_admin)]` on the whole admin router.
One place, not a check copy-pasted into every handler, because I will forget one.

**§4.4** The first account created in a fresh database becomes an admin. After that, only an existing
admin can promote anyone. An admin can't demote themselves if they're the last one left, otherwise
the system has nobody who can fix it. *(Amended — see ERRATUM E-2.)*

**§4.5** Admins should not see other people's actual spending. That's private, and there's no support
reason to look at it. Admin screens show counts and dates, not amounts or descriptions. If I change
my mind later I'd rather add it deliberately than find it was there all along.

## §5 — Knowing who's logged in

**§5.1** A JWT sits on the user's machine and my server never sees a list of them, so "how many
people are logged in" is not a question a stateless token can answer.

**§5.2** So there's a `sessions` table. On login I insert a row, and I put that row's id into the
token as the `jti` claim. The `get_current_user` dependency checks the row still exists and isn't
revoked, then bumps `last_seen_at`, throttled to once a minute so I'm not writing on every single
request.

**§5.3** Currently active means `last_seen_at` within the last 15 minutes and `revoked_at` is null.

**§5.4** This buys three things at once: the admin dashboard can count active sessions; signing out
actually invalidates the token instead of just deleting a cookie; and when an admin resets someone's
password, I revoke all their sessions in the same transaction, so the old token dies immediately.

**§5.5** That last one is the reason this isn't optional. A password reset that leaves the old
session working is not a password reset.

## §6 — Data model

**§6.1** Money is stored as an integer number of cents. Never a float. Floats can't hold 0.10 exactly
and summing them drifts, and this is an app whose entire job is adding numbers up.

**§6.2** `users` — id, email (unique, case insensitive), password_hash, display_name, role, currency,
is_active, created_at

**§6.3** `sessions` — id, user_id, issued_at, last_seen_at, revoked_at, user_agent, ip

**§6.4** `password_resets` — id, user_id, token_hash, expires_at, used_at, created_by_admin_id

**§6.5** `categories` — id, user_id, name, color hex, created_at. Each user owns their own set. Seed
eight sensible ones when an account is created.

**§6.6** `expenses` — id, user_id, category_id (nullable), amount_cents (BigInteger, must be greater
than zero), description, spent_on (Date), receipt_key (nullable), created_at, updated_at

**§6.7** `admin_audit_log` — id, admin_id, action, target_user_id, details (JSONB), created_at

**§6.8** Index `expenses` on `(user_id, spent_on DESC)` and on `(user_id, category_id)`. Index
`sessions` on `(user_id)` and on `(last_seen_at)`.

**§6.9** Deleting a user cascades to their categories, expenses, and sessions. It does not cascade to
the audit log, because the whole point of the log is that it survives.

## §7 — API

**§7.1 auth** — register, login, logout, current user, request a password reset with a token,
complete a password reset. *(Amended — see ERRATUM E-3.)*

**§7.2 categories** — list, create, delete. Deleting a category leaves the expenses alone and nulls
their category_id. I don't want to lose history because I renamed something.

**§7.3 expenses** — list with date range and optional category filter, create, update, delete, and a
summary endpoint.

**§7.4** The summary endpoint takes a date range and returns everything the dashboard needs in one
call: total, entry count, daily average, a breakdown by category, and one row per calendar day
including days where nothing was spent. Use `generate_series` for the empty days. I want the whole
dashboard to load in one round trip, not five.

**§7.5 receipts** — get a signed upload URL, attach the key to an expense, get a signed view URL,
delete.

**§7.6 admin** — list users with pagination and search, count active sessions, list active sessions,
revoke a user's sessions, issue a password reset, toggle is_active, change role, read the audit log.

**§7.7 health** — `/healthz` returns OK without touching the database, because that's what the load
balancer calls and I don't want a brief database hiccup convincing it that healthy containers are
dead. `/readyz` does check the database, for when I'm debugging by hand.

## §8 — How receipts work

**§8.1** The browser asks my server for a signed URL, uploads the file straight to S3 with it, then
tells my server the key. The file never passes through the container, so a large upload doesn't
occupy an ECS task or run into a request size limit.

**§8.2** `generate_presigned_url` doesn't make a network call, it's signed locally, so plain
synchronous boto3 is fine here even inside async handlers. Don't reach for aioboto3 for this.

**§8.3** Keys look like `receipts/{user_id}/{expense_id}/{uuid}.{ext}`. The server refuses to attach
a key whose prefix doesn't match, so nobody can point their expense at someone else's file. The
bucket blocks all public access and signed URLs expire in five minutes. JPG, PNG, WEBP and PDF only,
10 MB cap.

**§8.4** If `S3_BUCKET` isn't set the whole feature switches off gracefully instead of crashing. I
want to be able to run this locally without AWS credentials.

## §9 — Frontend

**§9.1** Pages: sign in and create account (same page, two modes), the dashboard, and an admin area
that only appears if the role says so. Hiding the admin link in the UI is cosmetic, the real check is
`require_admin` on the server for every request.

**§9.2** Dashboard pieces:
- Period picker with chips for this week, this month, last month, this year, plus custom dates
- **The category ribbon.** One horizontal bar split in true proportion to what each category cost,
  and clicking a band filters the list below. I want the chart and the filter to be the same object,
  not two controls I have to keep in sync
- A small bar per day across the range
- Entries grouped by date with a per-day subtotal
- Add expense as a panel that slides in from the right on desktop and up from the bottom on phones

**§9.3** Admin area: a user table with last active and status, an active-session count, and per-user
actions for reset password, force sign out, deactivate, change role. Plus the audit log.

**§9.4** Look and feel: paper and pine green, not the default blue SaaS dashboard. Instrument Serif
for display, Instrument Sans for body, IBM Plex Mono for every number. Tabular figures so columns of
money line up. Works down to phone width, keyboard focus visible, reduced motion respected.

**§9.5** Vite's dev server proxies `/api` to port 8000 so the session cookie behaves the same locally
as it will in production.

## §10 — Rules I don't want broken

**§10.1** Integer cents everywhere. Parse the incoming amount string with `Decimal`, then convert to
int cents in a Pydantic validator. Never let a float touch it. Convert back to a display string in
React, at render time only.

**§10.2** Every query filters on the user id from the verified token, never from anything the browser
sent. There should be no endpoint that can return a row without it. Admin queries are the deliberate
exception and they go through the admin module.

**§10.3** SQLAlchemy's expression language everywhere. If you ever reach for `text()`, bind the
parameters. No f-strings anywhere near SQL.

**§10.4** Session in an httpOnly cookie, SameSite=Lax, Secure in production. Not localStorage.

**§10.5** bcrypt at cost 12. On login, run the compare even when the email doesn't exist so response
timing doesn't reveal which emails have accounts.

**§10.6** Cast `SUM()` to BigInteger in the query. Postgres returns the sum of a bigint column as
numeric, which comes back to Python as a `Decimal`, and then it silently fails to serialise or mixes
badly with ints. Cast it and get an `int`.

**§10.7** Password reset tokens are stored hashed, single use, and expire in one hour.

**§10.8** Every admin action writes to the audit log in the same transaction as the change. If the
log write fails, the change rolls back.

**§10.9** Rate limit login and password reset harder than everything else. `slowapi` is fine for
this.

**§10.10** Pydantic does the input validation. Don't hand-roll checks that a schema constraint
already covers, and don't trust the frontend for any of it.

**§10.11** One `AsyncSession` per request, handed out through a FastAPI dependency. Never a
module-level session.

## §11 — Deployment

**§11.1** Multi-stage Dockerfile. First stage is `node:20-alpine` and builds the React app. Second
stage is `python:3.12-slim`, installs dependencies, and copies the built frontend in from the first
stage. Only the results carry over, not the Node toolchain.

**§11.2** Run as a non-root user. Use tini as the entrypoint so SIGTERM gets forwarded and ECS can
stop tasks cleanly. Handle shutdown in a FastAPI lifespan handler that disposes the engine, and
uvicorn will drain in-flight requests on its own.

**§11.3** Run uvicorn with `--workers 2` and let ECS handle scaling beyond that by adding tasks.
Don't put gunicorn in front, it's an extra layer I don't need here.

**§11.4** `DATABASE_URL` and `JWT_SECRET` come from Secrets Manager, loaded through a Pydantic
`BaseSettings` class. S3 access comes from the ECS task role, which boto3 picks up on its own. No
keys in the repo, no keys in the task definition. *(Superseded in part — see ERRATUM E-1.)*

**§11.5** Two IAM roles, and the distinction matters: the execution role is used by ECS before my
code exists, to pull the image and read secrets. The task role is used by my code once it's running.
Secrets permissions go on the execution role. S3 permissions go on the task role.

**§11.6** Run `alembic upgrade head` at container start, before uvicorn binds the port. Alembic takes
an advisory lock, so two tasks booting at once is safe. *(Factually wrong — see ERRATUM E-4.)*

**§11.7** I want a `docker-compose.yml` with a throwaway Postgres so I can run the whole thing
locally, and a GitHub Actions workflow that builds, pushes to ECR, and updates the ECS service, using
OIDC rather than stored AWS keys. *(Amended — see ERRATUM E-5.)*

## §12 — Out of scope, don't build these

**§12.1** No native mobile app. Website only.

**§12.2** No reading bank SMS. Browsers can't access the message inbox at all, and that route needs a
separate Android app I'm not writing.

**§12.3** No Account Aggregator or bank API integration. India's AA framework requires an RBI, SEBI,
IRDAI or PFRDA licence and I don't have one.

**§12.4** No pulling from Google Pay or Blinkit. Neither hands transaction data to third parties.

## §13 — Build order

1. `core` layer and the empty module skeleton, so the shape is right before there's code in it
2. SQLAlchemy models and the first Alembic migration
3. Auth, including the sessions table and the role column
4. Categories and expenses, with the summary endpoint
5. React dashboard and the add-expense panel
6. Admin module and admin UI
7. Dockerfile and compose, confirm the whole thing runs locally
8. S3 receipts
9. AWS deployment

*(Amended — see ERRATUM E-6.)*

## §14 — Later, not now

- Import a bank statement CSV to create many entries at once. This is the real fix for manual typing
  and it stays web-only, so it's the next thing after launch.
- Web app manifest so the site can be saved to a phone home screen
- Autocomplete on the note field from recent entries
- Editing an existing expense in the UI. The endpoint will exist, the screen won't.
- Monthly budget per category

---

## §E — ERRATA

**Errata govern over the text they correct.** Each cites the ADR that ruled it.

**E-1 · §2.3 and §11.4 — the deployment target changed.** "ECS Fargate behind a load balancer" and
"Secrets Manager" both bill, and the client subsequently ruled that nothing paid may be used. The
target is **ECS on EC2** (`t2`/`t3.micro`, free tier), **no load balancer**, **no NAT gateway**, and
**SSM Parameter Store** in place of Secrets Manager. → `SW-ADR-014`

**E-2 · §4.4 — first-admin bootstrap is gated.** As written, whoever finds a freshly deployed
instance first becomes admin. The claim is gated on a `BOOTSTRAP_ADMIN_EMAIL` environment variable.
→ `SW-ADR-021`

**E-3 · §7.1 — no self-service password reset in v1.** There is no email anywhere in §2, so a
self-service reset token has no delivery route. Only an admin may issue a reset; the token is shown
to the admin once and handed over out-of-band. → `SW-ADR-012`

**E-4 · §11.6 — Alembic does NOT take an advisory lock.** The premise is false. Partial
serialisation comes from the `alembic_version` row lock, but the race is real. `pg_advisory_xact_lock`
must be taken explicitly in `env.py`. → `SW-ADR-019`

**E-5 · §11.7 — the GitHub Actions workflow is not written by the build session.** The client builds
all CI/CD and AWS by hand, deliberately, to practise the DevOps role. The Dockerfile and compose file
are written by the build session, but late — not during the day-one proof. → `SW-ADR-005`,
`SW-ADR-011`

**E-6 · §13 — the build order gains a step 0.** A thin vertical slice is proven end to end — empty
database migrates, two users seeded, real browser login, user A reads their own row, **user B denied
at the database layer**, and the summary rule computing its expected value — before any feature work
begins. → `SW-ADR-009`, `SW-ADR-010`

**E-7 · §6.1/§6.2 — currency is fixed and snapshotted.** v1 is Indian Rupees only, stored as integer
paise. The `currency` column is kept on `users` and added to `expenses`, snapshotted at write time,
so a later currency change cannot silently reinterpret history. → `SW-ADR-013`

**E-8 · §2.4 — "no CORS to configure" is wrong for the S3 upload path.** §2.4's premise holds
for the API — one origin, no CORS. It is **false** for §8.1's direct browser-to-S3 upload, which
is a second origin. Without a bucket CORS policy every receipt upload fails in the browser with
an opaque error and no usable response body, so the application cannot even report why.
A bucket CORS rule is required. → `SW-ADR-069`

**E-9 · §6.6 — the money column is `amount_paise`, not `amount_cents`.** `SW-ADR-013` fixed the
product at Indian Rupees, whose minor unit is the paisa. A column named `cents` holding paise is
a comment that lies, which is the exact class of silent reinterpretation `SW-ADR-013` exists to
prevent. → `SW-ADR-029`

**E-10 · §8.1 — uploads use a presigned POST with a policy, not a bare presigned PUT.** §8.3
states a 10 MB cap and a type allowlist as facts. A plain presigned PUT enforces neither — the
signing server never sees the bytes — so an object can be stored with `Content-Type: text/html`
and later served as HTML from a signed URL. → `SW-ADR-047`
