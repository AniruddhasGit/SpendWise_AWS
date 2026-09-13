# AGENT_CONTRACT.md — the binding one-pager every coding session loads

> You are building SpendWise from this package. **This contract is BINDING.** It travels
> *in-package* because a session may load no project config at all, and the rules must reach it
> regardless.

## The nine rules

**1. `OPEN` means escalate, never invent.** If a question is not settled by this package or its
cited sources, you do **not** resolve it. Write a decision brief — question, minimal context,
2–4 costed options, a recommendation, and what would prove the recommendation wrong — and route
it one model tier up. **A plausible guess written into code is the primary failure this whole
document set exists to prevent.**

**2. Authority order on conflict.** raw `SRC-001` wording → an explicit client ruling → an
`APPROVED` ADR → `03 PRD` → `02 BRD` → `05 Bible` → everything else. **Stricter always wins.**
23 of the 155 ADRs are superseded or withdrawn — **check the ledger's `decision_status` before
citing one.** A superseded record is not authority, and citing one has already caused a defect on
this project once.

**3. DDL from migrations only.** No direct DDL against any database, ever. Consumers extend
`alembic/versions/`; nobody edits the baseline migration. Every migration that could lose data
implements `downgrade()` as an explicit `NotImplementedError` naming the restore runbook — a
`downgrade()` that has never run against populated data is decoration.

**4. `schema.sql`, `security.sql` and `TRACEABILITY.tsv` are GENERATED.** `datamodel.json` is the
spec of record. **A hand patch to a generated file is erased by the next build, silently**, and
every downstream check then passes on bytes that no longer carry the fix. Edit the spec, regenerate.

**5. The runtime role is not the owner.** `spendwise_owner` migrates and owns; `spendwise_app`
serves traffic and **must not** own a table, be superuser, or hold `BYPASSRLS`. The application
asserts all three against the catalog **at boot** and refuses to start otherwise. Never work
around that assertion — it is the only thing standing between the isolation guarantee and a
silent collapse.

**6. The request identity is set with a bound parameter.**

```python
await session.execute(text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user_id)})
```

**Never `SET LOCAL`** — it cannot take a bind parameter, so it would force the
f-string-near-SQL that `SRC-001 §10.3` forbids, on the hottest path in the application.

**7. Money is integer paise.** Parse with `Decimal` at the boundary, convert in a validator,
never let a float near it. `SUM()` returns `numeric` and cannot overflow — but the **mandated
cast back to an integer can**, which is exactly what the `<= 10^12` check keeps safe. Format for
display only at render time, `en-IN`, through one shared formatter.

**8. Reserved matters stop and wait.** Money above a stated ceiling · secrets · legal posture ·
anything irreversible or outward-facing · scope changes · **waiving any quality check**. No
delegation reaches these. Adopting the *stricter* option is not a waiver and needs no signature;
choosing the looser one is, and does.

**9. Status discipline.** Every artifact you touch keeps its status current: `RULED` (cited),
`PROVISIONAL` (a dependency outstanding), `OPEN` (escalate), `ASSUMED` (inference — never
hardens into a constraint).

---

## Standing facts you must not re-litigate

**Row-level security is on `expenses`, `categories` and `sessions`** — `FOR ALL` policies with
both `USING` and `WITH CHECK`, and `FORCE ROW LEVEL SECURITY`, because a table's owner bypasses
RLS otherwise, silently.

**`users` and `password_resets` are deliberately outside it** (`SW-ADR-097`, `SW-ADR-071`): a
policy keyed on the request identity cannot serve a lookup that happens *before* there is one —
sign-in and code redemption both do. Four compensating controls are MUSTs, listed in
`SW-ADR-097`. **This is a recorded waiver, not an oversight.**

**`admin_audit_log` carries no foreign keys** (`SW-ADR-083`) so it outlives its subjects, and is
immutable at the database (`SW-ADR-083`) — `UPDATE` and `DELETE` are revoked *and* a trigger
raises, so the refusal is visible rather than a silent permission error.

**The composite foreign key on `expenses` is `ON DELETE NO ACTION`, not `SET NULL`**
(`SW-ADR-072`). `SET NULL` on a composite key nulls **every** referencing column including
`user_id`, which is `NOT NULL`. The expenses service nulls `category_id` explicitly inside the
category-delete transaction.

**Migrations run with `SET LOCAL row_security = off`** on the migration connection only
(`SW-ADR-081`). Without it, `FORCE ROW LEVEL SECURITY` subjects the owner to the policies too, and
a data migration would report success while **silently affecting zero rows**.

**The day-one acceptance value is `75810` paise**, computed by the application from the seeded
fixture. A test asserting on its own fixture does not satisfy the gate.

## What is NOT in this package

The design system binds front-end engineering only and is **not** a schema source. Infrastructure
is the client's, by ruling — this package creates nothing in AWS and asks for what it needs
through `docs/30 Deployment/AWS_PREP_QUEUE.md`, in advance.
