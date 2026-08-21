# GOTCHAS — hard-won traps (symptom → root cause → fix)

Read this **before** building, not after debugging. Append every trap you hit, in this shape.
A trap recorded once is cheaper than the same trap found twice.

Entries marked **[UNPROVEN HERE]** were found by reading, not by hitting them on this project.
They are believed true and have not been observed failing here — which under K1 is exactly the
distinction that matters.

---

## Database & Postgres

- **A table's owner bypasses row-level security — silently.** RLS policies look correct, the
  denial test passes as the app role in one environment and fails in another.
  *Root cause:* the role that ran the migrations owns the tables, and owners bypass RLS unless
  forced. *Fix:* `ALTER TABLE … FORCE ROW LEVEL SECURITY` on every protected table, **and** a
  separate runtime role that does not own the tables, is not superuser, and lacks `BYPASSRLS`.
  **Check by querying the catalog, never by assuming.** [UNPROVEN HERE]

- **Local Postgres gives you superuser; RDS never does.** A migration that works on a laptop fails
  on RDS. *Fix:* build against the restricted role from day one. The three places they differ:
  superuser, forced SSL, and the allowed extension list. [UNPROVEN HERE]

- **`SUM()` of a `bigint` column returns `numeric`.** It arrives in Python as a `Decimal`, then
  either fails to serialise or mixes badly with `int` and produces a wrong total.
  *Fix:* cast to `BigInteger` in the query and get a real `int` back.

- **Alembic does NOT take an advisory lock.** Widely believed, not true. Two ECS tasks booting
  together can race on `alembic upgrade head`. *Fix:* take `pg_advisory_xact_lock` explicitly in
  `env.py`. **This was stated as a settled fact in the requirements dump and is wrong** — see
  `docs/00 SourceOfTruth/SRC-001` erratum E-4 and `SW-ADR-019`.

- **`db.t2/t3.micro` has roughly 110 max connections.** 2 uvicorn workers × pool size × N tasks
  adds up faster than it looks. *Fix:* size the pool deliberately; do not accept the default and
  hope. [UNPROVEN HERE]

## Web & auth

- **`slowapi` behind a load balancer rate-limits the load balancer.** Its default key is
  `request.client.host`, which behind a proxy is the proxy — so every user on earth shares one
  bucket and the limiter appears to work while protecting nothing.
  *Fix:* uvicorn `--proxy-headers --forwarded-allow-ips=<the proxy's subnet>`.

- **`slowapi`'s default storage is per-process.** With `--workers 2` across N tasks, "5 attempts per
  15 minutes" is really 5 × 2 × N. *Fix:* a shared store (Redis) — or accept it knowingly and
  **write down that you accepted it**, which is what this project did (`CONSTITUTION.md` Art X, `OPEN-RATE-01`).

- **bcrypt at cost 12 blocks the event loop.** ~300 ms of pure CPU inside an `async def` handler
  stalls every other request on that worker. On a 0.25-vCPU container a handful of simultaneous
  logins is a visible outage. *Fix:* `asyncio.to_thread`. Also: **bcrypt silently truncates
  passwords at 72 bytes** — reject or pre-hash, don't ignore it.

- **A cookie without `Secure` over plain HTTP is a login credential in clear text.** This project's
  free-tier deployment has no TLS (`SW-ADR-014`), so `Secure` is env-driven and off there. That is a
  recorded weakness with an expiry condition, **not** a default anyone should copy.

## Money & time

- **Floats cannot hold 0.10.** Summing them drifts, and this app's entire job is adding numbers up.
  *Fix:* integer minor units everywhere; `Decimal` only at the parsing boundary; format for display
  in React at render time only.

- **"This month" is a timezone question.** A server computing it in UTC for a user in IST is wrong
  by 5.5 hours at both boundaries. *Fix:* the browser resolves the period chip into explicit
  `from`/`to` dates and sends them. The server never guesses "this month".

- **"Daily average" has three defensible denominators** and they differ by 10×. Days elapsed, days
  with spending, or days in range. *Fix:* it is ruled — days **elapsed**, capped at today
  (`SW-ADR-010`), with a worked example and an expected value the day-one gate checks against.

## Process traps (already hit on this project)

- **A check that cannot fail looks exactly like a clean result.** The source method's own
  confidentiality gate reads a CRLF blocklist line-by-line, matches nothing, and prints "scrub OK".
  It has never refused anything on Windows. *Fix:* a repo-root `.gitattributes` with
  `* text=auto eol=lf`, **and** red-proof every gate — plant a violation, watch it fire, revert,
  verify the revert.

- **A requirements dump can state a false fact with total confidence.** Three did here (Alembic
  locking, and two rate-limiter assumptions). *Fix:* verify load-bearing technical premises before
  they become specification. A premise inherited without checking is a bug with a long fuse.

- **The client and the builder being one person removes the delay that catches bad answers.**
  There is no queue to make visible when the decider is also at the keyboard. *Fix:* every
  IRREVERSIBLE question gets a fresh zero-context second opinion before it is acted on (`SW-ADR-001`).

- **A blanket "you decide everything" instruction quietly repeals the constitution.** *Fix:*
  technical calls are the session's, reserved matters stay reserved, and reversible reserved matters
  get decided-then-batched for reversal rather than blocking (`SW-ADR-015`).

## The three audited admin GETs can never be served from a read-only path

`SW-ADR-135`. `/api/admin/users`, `/api/admin/sessions` and `/api/admin/audit` each write one
`admin_audit_log` row **per request**, inside the same transaction as the read, and the response is
serialised **only after `COMMIT`**.

So they are **primary-only, read-write**. Not a read-only transaction — the `INSERT` fails. Not a
replica — cross-node atomicity does not exist. Not a cache — a hit would disclose without its
one-row-per-request record.

This is written down because the optimisation is so obvious: *these are GETs, put them on a
read-only path.* Doing that silently breaks `SRC-001 §10.8`, and nothing would go red — the
response would look identical. An empty result still audits; the admin looked.

A 403 to a non-admin writes **nothing** here. The action allowlist is closed and has no
denied-attempt type; refused attempts belong to the request log (`P-OPS-05`) and `SW-ADR-104`.

## `set_config('app.user_id', …, true)` is TRANSACTION-local, and losing it is silent

`SW-ADR-136`. The third argument `true` scopes the setting to the current transaction. If any
repository opens a **second transaction**, the GUC is gone there — and every RLS-protected query
then returns **zero rows instead of erroring**.

That is the worst failure shape in this system: an empty dashboard is indistinguishable from a
person who has spent nothing. Nothing goes red. One `AsyncSession`, one transaction per request,
GUC set as the **first statement**, in the auth dependency.

Related: the session lookup itself runs under that policy, so it must come **after** the
`set_config`. `03_security_isolation.md` originally showed the reverse order, which returns zero
rows for every request ever made — authentication that never succeeds.

## A LEFT JOIN owner predicate belongs in `ON`, never `WHERE`

The day series uses `generate_series` LEFT JOINed to `expenses`. Put `e.user_id = :uid` in the
`WHERE` clause and the LEFT JOIN quietly degenerates to an INNER JOIN: the zero-spend days vanish,
the series shortens, and **only `SIT-E0-S9-05` notices** — the totals and the average stay correct,
so every other test still passes.

## The summary runs REPEATABLE READ, and it contains a write

`SW-ADR-142 F` put the three summary aggregates in one snapshot so the breakdown sums to the
headline. `SW-ADR-136` also has `get_current_user` bump `last_seen_at` — **a write, inside that
snapshot.**

Two concurrent requests on one session that both see the timestamp stale will both `UPDATE` the
row. Under `REPEATABLE READ` the loser gets **`40001`, could not serialize access due to concurrent
update**, and the request dies. Under `READ COMMITTED` it would simply block and succeed. `J-U-09`
documents the dashboard firing several requests at once, so this is a 500 on the dashboard,
intermittently, in production only.

The bump runs inside its own `SAVEPOINT`; on `40001` roll back to it and carry on. Losing one bump
is harmless — the transaction that won already performed it.

**And the level cannot be set with `SET TRANSACTION ISOLATION LEVEL`**, because `set_config` is the
first statement and PostgreSQL then raises `25001`. It is selected on the connection at checkout,
before `BEGIN`, from a route table — never from dependency-resolution order, which would open a
second transaction and silently return zero rows everywhere (`SW-ADR-143`, `SW-ADR-144`).

## `generate_ledger.py` takes Status from the BIBLE and will wipe the ledger

- **Re-running `docs/10 EngineeringLedger/generate_ledger.py` destroys every hand-edited `Status`
  and every `EvidencePath` in `engineering_ledger.tsv`.** The header says the ledger is derived and
  that "exactly one column is hand-edited: **Status**" — which reads as "Status is preserved". It
  is not. `main()` copies `Status` straight from the Bible row and rewrites `EvidencePath` to the
  literal `evidence/{ID}/`, so a regeneration silently reverts the entire build frontier to
  whatever the Bible says and deletes every note recording *why* a story is where it is.
  *Root cause:* two files hold the same column and the generator treats the Bible as the source.
  *Fix:* **edit the ledger by hand.** If the Bible's criteria change, sync the one row rather than
  regenerating. The ledger is NOT in `consistency_check.py`'s regenerate-and-compare list, so
  nothing catches this — it is the one derived artifact that is not verified by regeneration, and
  that is what makes running the generator so tempting and so expensive.

## Two ways a route-table test passes while examining nothing

Both were hit on 2026-08-21 writing `E6-S5`, in the same file, minutes apart.

- **`app.routes` is not the route table.** This FastAPI keeps each included router as an
  `_IncludedRouter` wrapper with no `.path` and no `.routes` — only `.original_router`. So
  `[r for r in app.routes if r.path.startswith("/api/...")]` returns **nothing** on an app with
  40 endpoints, and the test passes with an empty list. *Fix:* descend via `.original_router` —
  `tests/test_admin.py::flatten` already does it — **and assert the result is non-empty.** The
  descent alone is not the fix; without the non-empty assertion the next refactor silently
  re-empties it.

- **`from __future__ import annotations` makes every annotation a STRING.** Every module under
  `app/` has it. So `isinstance(param.annotation, type)` is `False` for every parameter of every
  handler, and a test that walks signatures looking for Pydantic models finds none — reporting
  success having inspected zero models. *Fix:* `inspect.signature(fn, eval_str=True)`, or
  `typing.get_type_hints(fn)`. **And count what you examined**: the only reason this was caught is
  that the test asserted `examined` was non-empty before asserting `offenders` was empty.

**The general rule both share:** a test that proves an ABSENCE must also prove it *looked*. Assert
the size of the population you searched, not just that the search came back clean — otherwise
"found no violations" and "found nothing at all" are the same green.
