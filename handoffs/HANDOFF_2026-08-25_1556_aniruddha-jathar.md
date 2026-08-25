# HANDOFF — 2026-08-25_1556

| | |
|---|---|
| **When** | Tuesday 25 August 2026, 15:56 IST |
| **Developer** | Aniruddha Jathar |
| **Repo** | `D:/SpendWise` |
| **Branch** | `main` |
| **Latest commit** | `a117bc7` — *This is detailed ci.yml file* |
| **Lane** | **OPS** — this session worked `.github/workflows/**`, not `app/**` |

---

## In progress — READ FIRST

**Nothing in the application is half-finished.** No application code was written this session. No
migration was started, no story was opened, no test was touched. `app/`, `client/`, `alembic/` and
`tests/` are byte-identical to where `2026-08-21_1605` left them.

**One thing is genuinely unresolved and it is in CI, not in the product:**

> **The `image` job's last observed state was RED, and the cause was Docker Hub, not this repo.**
>
> Run `32837108111`, job *Build the container image*, failed at `Dockerfile:22` with
> `failed to fetch oauth token: … 500 Internal Server Error` from `auth.docker.io`. That is the
> registry refusing to issue a pull token for `node:20-alpine`. Nothing in the Dockerfile, the
> workflow, or the application was involved.
>
> A re-run of the failed job was dispatched at 15:5x and **had not completed when this handoff was
> written.** Check it before assuming anything:
>
> ```
> gh run view 32837108111 -R AniruddhasGit/SpendWise \
>   --json jobs --jq '.jobs[] | "\(.conclusion)\t\(.name)"'
> ```
>
> If it is green, the failure was transient and the job is fine. If it is red again with the same
> 500, it is still Docker Hub. If it is red with a *different* error, that is a real finding and it
> belongs to the next session.

The other three jobs — `assemble`, `tests`, `secrets` — were observed **green** on that same run,
before and after the re-run was dispatched.

---

## What this session did

**Built `.github/workflows/ci.yml` from nothing.** The file that existed at the start was a
0-byte placeholder dated 18 August, which the previous handoff flagged as "delete it or claim it".
It is claimed. Four jobs now exist, each one written to answer a single question with a stated
"green means" and a stated "green misses".

| Job | Covers | Observed |
|---|---|---|
| `assemble` | lockfile installs on a clean runner · every file compiles · `app.main` imports · exactly one Alembic head | **green** |
| `image` | image builds (incl. the React bundle) · boots against a real Postgres · migrates an empty schema · answers `/healthz` | **red — Docker Hub 500** |
| `tests` | the suite subset needing neither PostgreSQL nor a browser | **green** |
| `secrets` | `gitleaks` over full history (`fetch-depth: 0`) | **green** |

**Three CI failures were hit and diagnosed, and each taught something worth keeping:**

1. **The first push failed in 0 seconds with no jobs at all.** Two `image:` keys existed in one
   file — the full smoke-test job had been pasted *below* `secrets` instead of replacing the
   build-only one, at four-space indent where jobs live at two. **PyYAML parsed that file happily**
   (duplicate keys are legal YAML; last one wins) while GitHub rejected it outright. The run's
   display name was `.github/workflows/ci.yml` rather than `CI`, because GitHub could not read the
   `name:` field. Fixed in `31eb7c4`.

2. **The container then refused to boot — and it was right to.** `alembic/env.py` raised:
   `MIGRATION_DATABASE_URL and DATABASE_URL are the same connection … one role for both means the
   runtime connection owns the tables, and an owner can disable FORCE ROW LEVEL SECURITY on itself`
   (`SW-ADR-081`). The workflow had handed the `postgres:16` service's single superuser to both
   variables. **The application enforced its own invariant against the CI configuration.** Fixed by
   creating `spendwise_owner` and `spendwise_app` — the two roles `0001_baseline.py` grants to by
   name — and pointing each URL at the right one.

3. **The third failure was Docker Hub returning a 500** — see *In progress* above.

**Line endings normalised to LF.** The file was CRLF throughout. Harmless for YAML itself, but
`run: |` blocks are shell scripts, and `\r` inside one fails in ways that are miserable to diagnose.

**Wrote `C:\Ideal\CI_DESIGN_PLAYBOOK.md`** — deliberately **outside this repo**, because it is
project-agnostic and will be reused elsewhere. Twelve sections: the four forces, nine calibration
factors, the three-question test, the tier model, a check catalogue of seven families with a
"what green does NOT tell you" column, over/under-writing symptoms, a per-check worksheet, and a
pre-flight checklist. The workflow's own comments reference it by section.

**`ci.yml` is now self-documenting.** Every job carries a header naming which catalogue family and
rows it covers, what green proves, and what green misses; the top of the file holds a coverage map
and an ASCII execution graph; the bottom holds a **NOT BUILT YET** block naming each remaining gap
and why it is still open.

---

## Current state

- **Working tree: clean** (before this handoff was written).
- **Application code: untouched.** Ledger unchanged — M0 9/10 · M1 8/8 · M2 8/8 · M3 8/8 · M4 6/6 ·
  M5 0/3 · M6 1/5. No Status was flipped, because nothing was built.
- **`tools/consistency_check.py`: PASS**, run before the first CI commit.
- **Day-one gate: still unproven.** Unchanged from the last session. It needs RDS.
- **Nothing deployed.** No AWS resource was created, touched, or observed. Every statement in this
  handoff about AWS remains *reasoned, not observed* (`SW-ADR-005`).

### Remotes — read this before pushing

**`origin` push now FAILS with `Repository not found`.**

The git identity was changed this session, at the client's request, to attribute commits to the
**AniruddhasGit** account:

```
user.name   Aniruddha Jathar
user.email  169955520+AniruddhasGit@users.noreply.github.com
```

The stored Windows credential followed. `AniruddhasGit` has no access to the private
`AniruddhaDynpro/SpendWise`, so `git push origin main` is rejected — not broken, just a consequence
of the switch, and recorded here rather than left to surprise someone.

| Remote | Repo | State |
|---|---|---|
| `personal` | `AniruddhasGit/SpendWise` | **at `a117bc7`** — current |
| `origin` | `AniruddhaDynpro/SpendWise` | **behind at `f320195`** — 3 commits, push rejected |

To sync `origin`, switch the credential back (`gh auth switch --user AniruddhaDynpro`, then clear
`git:https://github.com` from Windows Credential Manager) — **or decide that `personal` is now the
only remote that matters and say so.** That is a client call, not the session's.

Note also that pushing anything under `.github/workflows/` requires a token with the **`workflow`**
scope. Both accounts have it.

---

## Next ready steps

1. **Confirm the `image` re-run.** One command, above. Everything else assumes it.

2. **Set up RDS.** This is the largest unlock available and the top blocker. It releases **~209
   skipped tests**, the never-waivable **day-one gate**, and **all of M6** (`E6-S1`…`E6-S4`).
   When it exists, report **what actually was created** — endpoint, engine version, region, and
   whether `spendwise_owner` and `spendwise_app` both exist with the app role holding no
   `BYPASSRLS`. Under `COORDINATION.md`'s handshake the build session may only write down what
   someone observed, never what a queue says should exist.

3. **Two CI jobs that need nothing external** — roughly twenty minutes, worth doing while AWS
   provisions:
   - `tools/consistency_check.py` — already written, already has `--selftest`, free to run.
   - `actionlint` — **nothing currently checks `ci.yml` itself.** Failure #1 above is the argument:
     a local YAML parse said the file was fine and GitHub rejected it. Level-1 parsing is not
     level-2 linting.

4. **`E5-S3` (graceful absence of the receipts bucket)** — its acceptance criteria are explicitly
   the *no-bucket* case, so it needs neither RDS nor S3 and is buildable today.

5. **`E0-S10`'s remaining half** — the named-human signature on the fresh-clone evidence record.
   Closing it makes M0 10/10. Not the build session's to write.

---

## Blockers / decisions pending

| Blocker | Owner |
|---|---|
| **RDS credentials** — 209 skipped tests, the day-one gate, all of M6 | you |
| **S3 bucket** — `E5-S1` / `E5-S2` only | you (AWS) |
| **`E0-S10`'s named-human observation** | you |
| **`origin` unreachable under the new identity** — sync it or retire it | you |
| **Bible stories for six undocumented capabilities** — a scope decision | you |
| **`GET /api/admin/overview` has no authorising ADR** — recorded as not-determinable | you |
| **Local PostgreSQL on 5432** — still a false-green hazard for the isolation gate | you |

### One decision this session deliberately did NOT make

The CI Postgres now has **the same role separation as production** — an owner that migrates and a
runtime role that owns nothing. That means row-level security *could* bite there, which makes it
tempting to run the `db`-marked tests in CI and call isolation proven.

**It was left alone on purpose.** `SW-ADR-008` rules that the build happens against real RDS, and
`GOTCHAS.md` names a stand-in PostgreSQL as a false-green hazard for exactly that gate. Moving the
isolation proof onto a throwaway container is a decision with an ADR attached — it is not a CI
tweak, and it is not the session's to take.

---

## Resume protocol

1. `git pull` — note that `personal`, not `origin`, is the current remote.
2. Check the `image` re-run result before trusting any claim about CI in this document.
3. Read `CLAUDE.md` and `GOTCHAS.md`. Nothing here supersedes them.
4. Read `C:\Ideal\CI_DESIGN_PLAYBOOK.md` before adding any CI check — the workflow's comments cite
   its section numbers.
5. `.github/workflows/**` is **OPS** territory under `COORDINATION.md`. It was claimed deliberately
   this session, not drifted into. If a build session is running in parallel, it does not touch
   this file.
6. Then take the next ready unit of work — which, if RDS has arrived, is `E6-S1`.
