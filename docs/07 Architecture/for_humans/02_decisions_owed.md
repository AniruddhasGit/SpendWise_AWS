# Decisions still owed

**Two.** Everything else was ruled — 38 open questions escalated to a higher model tier on
2026-08-05 and adjudicated. These two are the ones no model may answer.

## 1. Your name on the Constitution — `OPEN-NAME-01`

**What it needs:** your exact full name, your role, and a backup decider. `NONE — accepted` is a
perfectly valid answer for the backup, and better than a blank.

**What it costs to leave open:** nothing technically. Everything continues. But all 128 decision
records carry a *"recorded while ungoverned"* caveat until it lands, and that caveat is on every
one of them.

**Why nobody can do it for you:** a name inferred from a git identity is not a signature.

## 2. What may enter an AI model — `OPEN-MODEL-01`

**What it needs:** a decision about what code and data may be given to an AI model, and which
vendors become data processors once real people use this.

**Working default, so nothing is blocked:** repository code, documents and made-up test data may
enter a model — they are already model-written and contain nobody's personal information. **No
real user data ever.** SpendWise has zero real users today, so nothing is blocked. This must be
revisited before the first real person signs up.

---

## Four rulings you may want to reverse

Each was made under your instruction to escalate rather than stall. **One message reverses any.**

| | What was decided | Why you might disagree |
|---|---|---|
| `OPEN-TZ-01` | The app's calendar is Asia/Kolkata | **Irreversible on the write path** — the moment an entry was submitted is never stored, so entries filed to the wrong day can never be found afterwards. **The window to change this closes when the first real expense is recorded.** |
| `OPEN-USERSRLS-01` | The accounts table is protected by the application only, not also by the database | This is formally a waiver of a quality check, which the rules reserve to you |
| `OPEN-PRUNE-01` | Dead sign-in records are deleted after 90 days | It deletes rows. Nothing else does |
| `OPEN-CAT-01` | The eight starting categories and their colours | It is product content, and content is yours. Groceries · Food & Dining · Transport · Rent & Utilities · Health · Entertainment · Shopping · Other |

## And one thing you must do before anything runs

`docs/30 Deployment/AWS_PREP_QUEUE.md`, items 0–9. **Item 0 is a billing alarm, and it comes
before anything that can bill.** Item 3 — the two database roles — is load-bearing: skip it and
the isolation gate passes for the wrong reason, which is worse than failing.
