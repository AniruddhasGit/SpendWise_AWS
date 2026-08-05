# 06 — Human decision queue

**Everything below is already decided and the build is not blocked.** This is the reversal list:
one message from you undoes any row. Nothing here needs an answer before code starts.

Two categories: **needs your signature** (formally outstanding), and **decided for you, flagged**
(taken under `SW-ADR-015`, reversible).

---

## A. Needs your signature — 2 items, neither blocking

### A1. `OPEN-NAME-01` — ratify the Constitution

`CONSTITUTION.md` is `v0.1-draft`, **UNADOPTED**. Until a named human signs the ratification block,
all 135 ADRs carry a "recorded while ungoverned" caveat, and BRD rows `N-ISO-02` and `N-OPS-01`
stay `PROVISIONAL` for that reason alone.

**What signing costs you:** ten minutes reading twelve articles. **What it buys:** the caveat
disappears and two requirements go from `PROVISIONAL` to `RULED`.

**If you never sign it:** nothing breaks. The build proceeds against the document as written; the
caveat simply stays.

### A2. `OPEN-MODEL-01` — legal and sub-processor posture

Whether an LLM provider processing your requirements text is a sub-processor you need to declare.
This is a legal question and no model may answer it. **Working default:** treated as out of scope
for a personal learning project with no third-party data. Gates nothing.

---

## B. Decided for you, flagged for reversal — 6 items

Each was decided under `SW-ADR-015` because stopping would have blocked the build. Each is
**reversible in one message**. They are listed worst-consequence-first.

### B1. `OPEN-TZ-01` — Asia/Kolkata, and this one is **irreversible on the write path**

`SW-ADR-089` / `SW-ADR-096`. The server computes "today" in Asia/Kolkata; `spent_on` is never
defaulted server-side.

**Why it is flagged hardest:** the submission instant is **never stored**. If this is wrong, rows
misfiled across a day boundary can never be identified afterwards — there is no column to
reconstruct the truth from. Every other row here can be undone; this one cannot, once rows exist.

**Reverse it before the first real expense is written, or not at all.**

### B2. `OPEN-USERSRLS-01` — `users` and `password_resets` sit outside row-level security

`SW-ADR-097` / `SW-ADR-071`. Login must read a user row by email *before* any verified identity
exists, so a policy keyed on the request identity can never serve it.

**This is a waiver of a quality check, which Art IX.6 reserves to you.** It was taken because the
alternative — a third database credential and a second connection pool for a pre-auth role — costs
real complexity for a learning project. The table holding every email and password hash is
protected by the application layer only, and four compensating controls are recorded.

**The stricter alternative is still available** and costs one more SSM parameter.

### B3. `OPEN-PRUNE-01` — rows get deleted

`SW-ADR-122`. Opportunistic pruning of `sessions` and `password_resets` at login: rows older than
90 days, up to 1,000 per table per run. The audit log is **never** pruned — it is immutable at the
database.

**Deleting data is reserved.** Flagged because it is your data being deleted, on a schedule nobody
watches.

### B4. `OPEN-CAT-01` — the eight seeded categories

`SW-ADR-092`. Food, Transport, Shopping, Bills, Health, Entertainment, Education, Other — with
fixed colours and order. **This is product content**, not a technical decision, and you may simply
prefer different ones. Changing them is a one-line seed edit before first run.

### B5. Uncategorised is `#948c87`, not `#a8a29e`

`SW-ADR-131`. The specified colour measured **2.36:1** against paper, below the 3:1 floor a UI
component needs. It was darkened within the same hue to **3.09:1**.

Flagged only because it changes something you can see. Adopting a stricter option is not a waiver
(Art IX.6), so it needed no signature — it needed a record, which it now has.

### B6. Constitution counts refreshed

`SW-ADR-133`, ruled at the Fable 5 escalation tier. Art I.1 said "the **22 records**"; there are
135. Art II.3 said seven errata; there are ten. Art III.3 said the derivation documents "do not yet
exist"; ten of them do.

**No rule changed** — Art I.1 is now stated as *location plus ledger* rather than a number, so it
cannot go stale again. Flagged because amending the Constitution is reserved and you may take the
view that a count refresh is an amendment. **If you do:** the fix is not to restore the stale
figures but to mark them stale in place with a pointer to the ledger — Art II.6 forbids the
unmarked contradiction either way.

---

## C. Owed to you as advance notice — the AWS prep queue

Not decisions; **work only you can do**, because the build session never touches AWS
(`SW-ADR-005`). `docs/30 Deployment/AWS_PREP_QUEUE.md` carries the full list, each item with a
*needed by*.

Four were added at this exit gate because ADRs asserted they were queued and they were not:

| # | Item | Needed by |
|---|---|---|
| 11 | CloudWatch alarm on `RunningTaskCount < 1`, SNS topic, subscription **confirmed** | first deploy — and force it once |
| 12 | S3 lifecycle rule expiring `staging/` after 1 day | first receipt upload |
| 13 | ECS deployment config: min-healthy **0**, max 100 | first **re**deploy — at the default it deadlocks silently |
| 14 | Third SSM parameter `MIGRATION_DATABASE_URL` as `SecureString` | first deploy |

Item 14 is the one most likely to bite: the boot sequence runs migrations under the **owner** role
and serves traffic under the **runtime** role, then asserts at startup that the runtime role owns
no table. Two roles with different passwords are two connection strings. The queue said "both
parameters", which quietly assumed one.

---

## What happens if you answer none of this

The build proceeds. Every row above has a working default and a record saying so. The only thing
you lose is the chance to reverse **B1** before it becomes unreversible.
