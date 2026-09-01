# HANDOFF — 2026-09-01_1302

| | |
|---|---|
| **When** | Tuesday 01 September 2026, 13:02 IST |
| **Developer** | Aniruddha Jathar |
| **Repo** | `D:/SpendWise` |
| **Branch** | `main` |
| **Lane** | BUILD (client + tests + docs) — and OPS earlier in the same stretch |

---

## In progress — READ FIRST

**Nothing is half-finished. No gate is red.**

For the first time in this project's life the **entire suite is green**:

```
pytest                      473 passed
pytest tests/browser         55 passed      <- CV-16, never green before
consistency_check.py        PASS  (--selftest: 18/18 checks observed firing)
contrast.py                 light 26/26 · dark 26/26
npm run lint:tokens         PASS
```

### ⚠️ Still outstanding, and it is security

> **Rotate the AWS access key.** It was pasted into a chat window on 2026-08-25 and its IAM user
> `AWS_cli_dynpro` holds **`AdministratorAccess`** over account `944483082287` — IAM and billing
> included.
>
> ```
> IAM → Users → AWS_cli_dynpro → Security credentials → Access keys → Deactivate → Delete
> aws configure --profile spendwise     # replacement, typed at the prompt
> ```
>
> Also delete `CLI_access_key_claude.txt`, the two credential CSVs, and `~/Downloads/dyone_keys.txt`.
> None are inside the repo — verified.

---

## What this session did

### 1. Sign out moved beside the account it signs out of

It sat alone in a page footer — the one place nobody looks for it. Now under the name and email in
the rail. **Moved, not added**, so `data-testid="sign-out"` stays unique: two browser criteria find
it by that id, and one asserts a background control cannot take focus through `inert`, which the
rail satisfies as well as the footer did.

### 2. The browser suite had never passed — one line in a fixture

Verifying that move turned up why. `tests/browser/conftest.py` spawns its own uvicorn with
`SPENDWISE_DOTENV=0`, so `.env` is not read and `RATE_LIMIT_ENABLED` falls back to its field default
of **true**. The suite registers dozens of accounts against `RATE_LIMIT_REGISTER_PER_MIN=5`, and
**34 setups died on a 429 before asserting anything.**

The fixture predates `E1-S6`, which added rate limiting, and nothing re-ran it afterwards.
`settings.py` already states the intent — *"the test suite turns it off for everything except the
rate-limit tests"* — so this is one line making the browser fixture obey a rule the in-process suite
already followed. The limits stay covered in-process by `test_rate_limits.py`.

**`CV-16` — the day-one gate observed in a real browser — has now gone green.** The 2026-08-25
handoff recorded it as never run; that is closed.

### 3. The Swiss restyle, and the ruling it forced

The client's third visual revision: hairline rules, no shadows, square corners, oversized display
type, mono uppercase micro-labels. No colour moves; **no `.jsx` file changed for it**.

**It contradicted an approved record on arrival.** `SW-ADR-147` **D** pinned the contrast floor to a
glass alpha of `0.78`; the restyle sets every alpha to `1` and the blur to `0`. A browser criterion
enforced the old rule directly, and **no code change could make it green** — satisfying it meant
abandoning the restyle. Raised with three options and stopped (Art IX.2). The client chose to keep
the restyle.

**`SW-ADR-154`** records that ruling and **amends** `SW-ADR-147` D rather than withdrawing it. The
principle — a floor is computed, never asserted — is untouched and now enforced more directly:

| | Old criterion | New criterion |
|---|---|---|
| asserted | the background string contains `rgba` | painted ink-on-card ratio ≥ 4.5:1 |
| computes a ratio | **no** | yes, WCAG 2.1, in the browser, both themes |
| catches an unreadable card | **no** | yes |

**Red-proofed both ways before being trusted.** Forced translucent it names the alpha; forced
opaque-but-3.46:1 it names the ratio; reverted it goes green.

### 4. Two defects in the restyle, fixed rather than ruled around

- **`.periods` carried `width: max-content`**, defeating `app.css`'s `flex-wrap: wrap` and pushing
  the page **222px past a 375px window**. Now `fit-content` + `max-width: 100%`.
- **`.entry-meta` had been added to the mono-uppercase label list** although it is not a label
  class. It renders a person's own category name, their email in the rail and the admin table, the
  `days-elapsed` figure the gate reads, and every chart caption. **An address stored as
  `a@spendwise.test` was displayed as `A@SPENDWISE.TEST`; a category typed as `Coffee` came back as
  `COFFEE`.** The app was changing what people had written. Six browser criteria caught it,
  including the gate's.

### 5. One ADR broke fourteen cross-references, and the checker found all of them

`consistency_check.py` failed immediately on the new record: `SW-ADR-147` carried no amendment
banner (Art II.6), `docs/README.md` had drifted, and four documents still claimed 153 ADRs
(`CLAUDE.md`, the PRD, `AGENT_CONTRACT.md`). All corrected. `--selftest` then observed **18/18**
checks firing on a planted violation, so the PASS is earned rather than assumed.

---

## Current state

- **Working tree clean.** Two commits this session plus this close-out.
- **Ledger unchanged** — M0 9/10 · M1 8/8 · M2 8/8 · M3 8/8 · M4 6/6 · M5 0/3 · M6 1/5. No Status
  flipped: `CV-16` going green is evidence toward `E0-S10`, not a story completed. **The named-human
  observation and the deliberate RLS red-proof are still owed**, and until both exist M0 stays 9/10.
- **AWS**: RDS `spendwise-db` (PostgreSQL 17.9, `ap-south-1`) live, two databases, two roles,
  firewall admitting one IP. `$20/month` budget with a forecast alarm.
- **Nothing deployed.** ECR, ECS and SSM untouched.
- **CI**: `assemble`, `tests`, `secrets` green; `image` last observed cancelled by the concurrency
  rule, its true state unverified.

---

## Next ready steps

1. **Rotate the access key.** Before anything else.
2. **Red-proof the day-one gate with a named human.** Disable the RLS policy on purpose, watch the
   isolation test go red, revert, verify the revert. Plus the four-line evidence record and its
   signature. That closes `E0-S10` and makes **M0 10/10** — everything else it needed now exists.
3. **`E6-S1`** — the log deny-list. The M6 frontier, unblocked since RDS arrived.
4. **`E6-S2` … `E6-S4`**, chained behind it.
5. **Fix `generate.py`** so `rds_bootstrap.sql` regenerates correctly — three defects recorded under
   AS BUILT in `AWS_PREP_QUEUE.md`.
6. **`consistency_check.py` and `actionlint` as CI jobs.** Neither needs anything external.
7. **`E5-S3`** — graceful absence of the receipts bucket. Needs no S3.

---

## Blockers / decisions pending

| Blocker | Owner |
|---|---|
| **Rotate the exposed admin access key** | you — today |
| **`E0-S10`'s named-human observation + RLS red-proof** — the only thing between here and M0 10/10 | you |
| **S3 bucket** — `E5-S1` / `E5-S2` only | you (AWS) |
| **Bible stories for six undocumented capabilities** — a scope decision | you |
| **`GET /api/admin/overview` has no authorising ADR** | you |

---

## Resume protocol

1. `git pull`. Both remotes should be current after this close-out.
2. Rotate the key if it is still alive.
3. Read `CLAUDE.md` and `GOTCHAS.md`.
4. **Confirm RDS is reachable — the security group allows exactly one IP and home IPs move:**
   ```
   curl https://checkip.amazonaws.com
   aws rds describe-db-instances --db-instance-identifier spendwise-db --profile spendwise
   ```
   If the app cannot connect, check that rule before anything else.
5. Run the app: `python -m uvicorn app.main:app --port 8000`, after
   `python tools/reset_and_seed.py` if you want accounts. `docs/aws/rds.html` explains the database.
6. Then `E6-S1`.

---

## A note on how two of these were found

Neither the fixture defect nor the uppercased email was reported by anyone. Both surfaced because a
test was run that had not been run before, and because the failures were read rather than silenced.
The uppercase one is the more interesting: it would never have appeared in a screenshot review —
`A@SPENDWISE.TEST` looks like a design choice. It took a criterion asserting the exact stored string
to show that the application had started editing its users' own data.
