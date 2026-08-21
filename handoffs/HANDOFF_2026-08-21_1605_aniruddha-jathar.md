# HANDOFF — 2026-08-21_1605

| | |
|---|---|
| **When** | Friday 21 August 2026, 16:05 IST |
| **Developer** | Aniruddha Jathar (`aniruddha-jathar`, git `AniruddhaDynpro`) |
| **Repo** | `D:/SpendWise` — **moved from `D:/Project/SpendWise`**, which every earlier handoff names |
| **Branch** | `main` |
| **Latest commit** | `6dbb2d0` — *E6-S5 done under the client's ruling, and the API spec catches up with the product* |
| **Previous handoff** | `handoffs/HANDOFF_2026-08-06_0442_ani87.md` (a different machine and user token) |

---

## What this session did

Six commits. **`M1` closed, `M6` opened, the container exists, and three documentation defects that
had been true for weeks were found and two of them fixed.**

### `CR-002` — the visual identity changed (`SW-ADR-152`)

The client supplied a design bundle reversing the visual half of `SRC-001 §9.4`: paper-and-pine
became greenish-white / olive / near-black, Instrument Serif / Instrument Sans / IBM Plex Mono
became Bricolage Grotesque / DM Sans / JetBrains Mono. `SRC-001` is fingerprinted, so it is a change
request with a superseding record, not an edit. **Its accessibility clauses were not reversed and
still bind.**

**Zero screen or component files were edited.** The whole re-skin is a token swap plus one additive
stylesheet, possible only because the bundle kept the token *names*. `main.jsx` gained three lines
(the import) exactly as the bundle's step 2 instructs.

Three defects the bundle shipped with:

1. **`--sw-cat-uncat` measured 2.99:1 against a 3.0 floor** — a fail by 0.01. The bundle listed the
   nine bands under "do not change" and predicted `--sw-border-strong` would be tightest; it was
   right about that (3.33:1) and wrong about which pair would fail. **The band never moved; the
   paper under it did.** Darkened within the hue to `#928a85`, 3.07:1, hue drift 0.00°. `#938b86`
   also cleared at 3.029:1 and was rejected — 0.029 of headroom is how `SW-ADR-147` happened.
2. **`U+20B9` (₹) is in `latin-ext`, not `latin`.** The bundle's one-file-per-family `@font-face`
   would have rendered every rupee sign from a fallback beside digits from JetBrains Mono, in an
   application about columns of money. Six woff2 files ship, two subsets per family, with their OFL
   licences (the OFL requires the licence to travel with the font). **Related: there was no
   `@font-face` anywhere in this repo before now** — the families were named and never loaded, so
   every screenshot under `evidence/` predating today shows OS fallbacks.
3. **The one that would have shipped.** After fixing the token, `contrast.py` went green at 3.07:1
   for a colour the app never draws: `Ribbon.jsx:119` and `Donut.jsx:51` paint `b.color` from the
   API response, so the rendered value is `UNCATEGORISED_COLOR` in `summary.py`. Three artifacts
   held that hex and the tool reads one. Fixed in all three plus the generated fixture and the
   day-one assertion; `consistency_check` gained **`band-colour-agreement`**, red-proofed.

### `E1-S6` — rate limits, with numbers. **M1 is 8/8.**

Until this commit every auth endpoint was unthrottled. Two bugs the tests caught:

- **The arithmetic.** `effective // workers` reproduces six of `SW-ADR-128`'s seven
  (effective, configured) pairs and gets registration wrong — `5 // 2 == 2` where the ADR says 3.
  Ceiling reproduces all seven. The test asserts against the ADR's own table rather than a rounding
  rule someone preferred, which is the only reason it surfaced.
- **The limiter ran AFTER the database.** Declared as an endpoint parameter it sat after `db` in the
  signature, so every throttled request checked out a connection before being refused. Moved to
  route-level `dependencies=[...]` (the shape `require_admin` already uses). AC1 asserts the db stub
  was reached 10 times across 11 attempts.

`[JUDGMENT CALL]` `SW-ADR-015`: uses `limits`, not slowapi's decorators. `SRC-001 §10.9` says
"slowapi is fine for this" — permission, not mandate — and this is the engine slowapi wraps, same
in-process store, so `SW-ADR-128`'s accepted weakness is unchanged. The decorator form cannot do
dual keying, cannot emit the closed envelope, and hides the reset time `Retry-After` needs.

### `range.required` — a rule that could never fire

Specified since the contract was written and unreachable. Both summary endpoints declared `from`
and `to` as **required** query parameters, so FastAPI refused before any rule here ran and every
caller got `field.required` — the exact G2 condition the contract names. One shared `require_range`
helper, because `CR-001 §2` requires the two endpoints to **be** the same rules, not merely agree.

**Why it survived 224 tests:** there was a test, and it asserted only that the two endpoints answer
*identically* — which they did, both wrongly.

### The Dockerfile (`SW-ADR-011`)

Two stages, `node:20-alpine` → `python:3.12.10-slim`, patch pinned. **Verified by building and
running it**, not by reading it: uid 999 non-root, no node/npm (563MB), `spa.py` resolves
`/app/client/dist` and it exists, tini is PID 1, curl present (the slim base ships none and
`SW-ADR-127` writes the health check as `curl -f …`). With an unreachable database it **exits 1,
does not retry, and `/healthz` has no listener** — `SW-ADR-093`'s "before uvicorn binds the port",
demonstrated. 16 static tests, including one asserting the entrypoint's `--workers` matches
`settings.UVICORN_WORKERS`, because the rate limiter divides by it.

### `E6-S5` — stopped, escalated, ruled, then built

Its criteria said *"no endpoint lets a person change their own email, display name or password"*.
Two thirds was false of the shipped product and **the falsity was APPROVED** (`SW-ADR-148` C and D);
a third clause was narrowed by soft delete (`SW-ADR-150`). The session marked it `Blocked`, wrote
the finding, and asked rather than editing the definition of done to match what was built.

**The client ruled option A** (narrow the text, change no code) → `SW-ADR-153`. 10 tests, every
detector red-proofed.

**Two of those tests were vacuous on first write** and both are now in `GOTCHAS.md`:
`app.routes` is not the route table (FastAPI hides endpoints behind `_IncludedRouter`), and
`from __future__ import annotations` makes annotations strings so a signature walk inspects nothing.
Both caught only by asserting the searched population was non-empty **before** asserting it was
clean.

### Seven shipped routes were missing from the API spec of record

The new wording named `DELETE /api/auth/me` and tripped `route-contract`. The audit found seven
routes served but absent from `contract.json` — the file the PRD's route table is *generated* from:
`PATCH /me`, `POST /password`, `POST /deactivate`, `DELETE /me`, `GET /export`,
`GET /admin/overview`, `GET /admin/users/{id}/spending`.

It hid because `route-contract` runs one way only. New **`route-coverage`** check parses the
routers' decorators with `ast` (statically, so it still runs on a bare clone) and fails on
served-but-undocumented; it also fails on extracting zero routes. All seven added with the four
model definitions they reference; PRD, `error_codes.md` and `expected_summary.json` regenerated;
the §6 count moved 28 → 35 by itself. **The day-one gate still asserts `75810` through it.**

---

## Current state

**Working tree clean** except `workflows/` — see *In progress*. **`personal/main` == `HEAD` ==
`6dbb2d0`.**

| Gate | Status |
|---|---|
| `py -m pytest` | **262 passed, 209 skipped, 2 failed** — both failures need a live database |
| `consistency_check.py` | **PASS** |
| `--selftest` | **18/18** red-proofed (was 16 at session start) |
| `contrast.py --check` | **PASS** — light 26/26, dark 26/26 |
| `sync_tokens.py --check` · `generate_api.py --check` | **PASS** |
| `npm run lint:tokens` · `npm run build` | **PASS** — 24 files, 51 modules |
| `docker build` | **PASS** — image builds, runs, and refuses to serve a half-migrated schema |

**The two failures are environment, not code**, and were failing before this session's changes:
`tests/browser/test_the_website.py::test_healthz_and_readyz_answer_over_http` and
`tests/test_gate_redproof.py::test_force_is_on_for_every_protected_table_afterwards`. Both need a
reachable `spendwise_test`.

### Environment built this session, from nothing

Python **3.12.10** installed (the machine had only 3.13/3.14; `SW-ADR-016` locks 3.12), `.venv`
created, `requirements.lock` installed, `npm install`, and Playwright's Chromium — which turned
**54 errors into clean skips**.

`.env` is a **PLACEHOLDER** pointing both URLs at `db.invalid` (RFC 2606, cannot resolve), so every
`db`-marked test SKIPS rather than passing for the wrong reason. Replace it with
`py tools/set_credentials.py`.

### ⚠️ A real PostgreSQL is running on this machine

**Port 5432, PID 7020.** The placeholder originally pointed at `127.0.0.1:5432` and the only thing
that stopped the suite connecting was a wrong password. `GOTCHAS.md` records why that matters:
local Postgres hands you superuser, superuser bypasses RLS, and the isolation gate would go green
for the wrong reason on the single guarantee this product exists to make. Repointing at
`db.invalid` also cut the suite from **366s to 46s** (NXDOMAIN fails in 0.03s; a refused port took
2s, times 209 skips).

**Deployed:** nothing. The image has been built and run locally; it has never left this laptop.

---

## In progress — READ FIRST

**Nothing is half-finished.** No red gate, no partial migration, no stranded branch.

One item deliberately left untracked: **`workflows/ci.yml`** — an empty 0-byte file dated 18 August
that predates this session. `COORDINATION.md` puts `.github/workflows/**` in the **OPS** lane, so
the build session did not commit it. Delete it or claim it; it is not ours.

**Both remotes are in sync at `b22c093`.** This was corrected after the handoff was first
written: it originally recorded `origin` as 6 commits behind and deliberately left alone, and the
client then asked for everything pushed. Amended rather than left standing, because a handoff that
describes a state the repo is no longer in is worse than no handoff.

**Two GitHub accounts, and only one works at a time.** `AniruddhasGit/SpendWise` is the main repo
(`personal`); `AniruddhaDynpro/SpendWise` is `origin` and is **private to the other account**. Git
authenticates as whichever `gh` account is active, so a push to the one you are not signed in as
fails with a bare *"Repository not found"* — which reads like a deleted repo, not an auth problem.
That cost a confusing minute today.

    gh auth switch --user AniruddhaDynpro && git push origin main
    gh auth switch --user AniruddhasGit   && git push personal main

`gh auth status` shows which is active. Left active as **`AniruddhasGit`**, the main repo.

---

## Next ready steps

1. **`E6-S1` — the log deny-list, red-proofed.** The M6 frontier. Its AC plants a reset code and a
   password through the **real** issue and sign-in paths and asserts they never reach stdout — so it
   needs a live database. First thing that unblocks when RDS returns.
2. **`E0-S10`'s remaining half.** The fresh-clone run into an empty directory with a new virtualenv
   — *which this session performed* — plus the four-line evidence record signed by a **named human**.
   That signature is not the build session's to write. Closing it makes **M0 10/10**.
3. **`E6-S2`…`E6-S4`.** Chained behind `E6-S1`; all need a database.
4. **M5 receipts.** `E5-S1` and `E5-S2` need the S3 bucket. **`E5-S3` (graceful absence) needs no
   bucket** — its AC is explicitly the no-bucket case.
5. **Bible stories for six capabilities shipped after `GOAL_07`** — `PATCH /me`, password change,
   deactivate, delete, export, admin overview. Authoring them is a scope decision, so it is the
   client's to ask for. Until then those seven contract entries carry `spec: []` and
   `GET /api/admin/overview` has **no authorising ADR at all**, both recorded as `OPEN` rather than
   invented.

---

## Blockers / decisions pending

| | Owner |
|---|---|
| **RDS credentials** — 209 skipped tests, the day-one gate, and all of M6 | you |
| **S3 bucket** — `E5-S1` and `E5-S2` only; the M6 dependency on it is sequencing, not technical | you (AWS) |
| **`E0-S10`'s named-human observation** | you |
| **Bible stories for the six undocumented capabilities** — a scope decision | you |
| **`GET /api/admin/overview` has no authorising ADR** — recorded as not-determinable | you |
| **Local PostgreSQL on 5432** — a false-green hazard for the isolation gate | you |
| **Deployment** — image builds; ECR/ECS/SSM untouched | you |
| **`origin` 6 commits behind** — deliberate; say if you want the accounts synced | you |

---

## Resume protocol

```
git pull
cd D:\SpendWise                       # NOT D:\Project\SpendWise — the repo moved
py tools\set_credentials.py           # replace the placeholder .env with real RDS
.venv\Scripts\python -m pytest -q     # expect 262+ passed once the database is reachable
.venv\Scripts\python tools\consistency_check.py --selftest   # expect 18/18
```

Then read **`CLAUDE.md`** → **`GOTCHAS.md`** (four new traps this session, three of them about
tests that pass while examining nothing) → **`docs/12 DesignReview/`** (two findings, both
RESOLVED, both worth reading for the pattern) → **`docs/10 EngineeringLedger/engineering_ledger.tsv`**.

**Do not run `docs/10 EngineeringLedger/generate_ledger.py`.** It takes `Status` from the Bible and
rewrites `EvidencePath`, so it would wipe every hand-edited status and note in the ledger. It is the
one derived artifact `consistency_check` does not verify by regeneration, which is what makes
running it tempting. Recorded in `GOTCHAS.md`.

If the suite skips en masse with *"spendwise_test unreachable or not migrated"*, check your public
IP against the RDS security group before assuming anything is broken.

To look at it: `.venv\Scripts\python -m uvicorn app.main:app --port 8000` from the repo root.
