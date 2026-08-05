# SpendWise — Business Requirements Document

| Field | Value |
|---|---|
| Version | v0.1-draft |
| Decision status | **NOT_DECIDED** (fail-closed — binds nothing until ratified) |
| Release status | NOT_RELEASED |
| Drafted | 2026-08-05 from `SRC-001`, `SRC-002` and the 90 records in `docs/01 ADR/` |
| Governed by | `spendwise-constitution@0.1.0` (UNADOPTED — see `OPEN-NAME-01`) |

---

## §1 — Reading rules and provenance grammar

**Every requirement carries a `[SRC:]` tag.** No tag means `ASSUMED`, and an `ASSUMED` statement
is inference — it can never harden into a `MUST` (`CONSTITUTION.md` Art II.5).

| Status | Meaning |
|---|---|
| `RULED` | decided, with a citation |
| `PROVISIONAL` | written down, a ruling still outstanding — proceeds, but may move |
| `OPEN` | genuinely unruled. **Escalate, never invent.** |

**This document is business intent only.** No technology, no schema, no endpoints. "A person can
see what they spent this month" belongs here; how that is computed belongs in `03 PRD`.

**On conflict** (Art II.1): raw `SRC-001` wording → a client ruling → an `APPROVED` ADR → this
document. Stricter always wins. Where `SRC-001` and an ADR disagree, the ADR is named inline.

---

## §2 — Scope and envelope

**In scope.** Everything in `SRC-001` §1–§11 as corrected by errata `E-1`…`E-10`, plus the 90
records in `docs/01 ADR/`.

**Hard exclusions** — MUST NOT enter scope `[SRC: SRC-001 §12]`:
no native mobile app · no reading bank SMS · no Account Aggregator or bank API integration ·
nothing pulled from Google Pay or Blinkit. Each was excluded for a stated reason: the browser
cannot reach a message inbox, and India's AA framework requires a licence the client does not hold.

**Deferred, not cancelled** `[SRC: SRC-001 §14]`: bank-statement CSV import · a web app manifest ·
note autocomplete · the expense-edit *screen* (the capability exists; the screen does not) ·
per-category budgets.

**Removed from scope after `SRC-001` was written:**
self-service password reset `[SRC: SW-ADR-012]` — there is no email anywhere in the stack, so a
token would have no delivery route. Recovery is administrator-issued.

**Win condition — define victory, then stop** `[SRC: CONSTITUTION.md Art I.5]`. A person signs up,
logs an expense, sees a correct dashboard; a second person cannot see the first person's money,
proven at the database layer; an administrator can reset a password and force a sign-out; it runs
on AWS from a container the client deployed by hand. Past that line is fast-follow.

---

## §3 — Who this is for

| Persona | What they are trying to do | Notes |
|---|---|---|
| **Person** (`user`) | Record what they spend without friction, and understand where it went. | The only persona whose goals the product actually serves. |
| **Administrator** (`admin`) | Keep accounts working — unlock someone, sign someone out, deactivate a leaver. | Exists for **one stated reason**: "I need someone to be able to reset a password when a user locks themselves out" `[SRC: SRC-001 §1]`. |

An administrator is also a person, with their own spending `[SRC: SRC-001 §4.2]`.

**The administrator is deliberately not powerful.** They can manage *accounts* and cannot see
*money*. That constraint is a stated product value, not an oversight — see `R-PRV-02`.

---

## §4 — Business requirements

### E1 — Accounts and access

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-ACC-01` | A person can create their own account and start using the product immediately. | `SRC-001 §1`, `§7.1` | RULED |
| `R-ACC-02` | A returning person can sign back in. | `SRC-001 §7.1` | RULED |
| `R-ACC-03` | Signing out genuinely ends the session — it does not merely hide it. | `SRC-001 §5.4` | RULED |
| `R-ACC-04` | The product knows who is currently signed in, and can end any session on demand. | `SRC-001 §5.2`, `§5.3` | RULED |
| `R-ACC-05` | A person who cannot get in is recovered by an administrator, out of band. There is no self-service route. | `SW-ADR-012` | RULED |
| `R-ACC-06` | The very first account in a new deployment becomes the administrator, and only a nominated address may claim it. | `SRC-001 §4.4`, `SW-ADR-021` | RULED |
| `R-ACC-07` | How long a person stays signed in before being asked again. | `SRC-001 §5` | **OPEN** — `OPEN-SESSION-01` |

### E2 — Recording what was spent

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-REC-01` | A person records a single act of spending: how much, when, and optionally what it was for and which category it belongs to. | `SRC-001 §6.6`, `§7.3` | RULED |
| `R-REC-02` | Money is Indian Rupees, and the amount recorded is exactly the amount typed — no drift, ever. | `SRC-001 §6.1`, `SW-ADR-013` | RULED |
| `R-REC-03` | A person can correct or delete anything they recorded. | `SRC-001 §7.3` | RULED |
| `R-REC-04` | A person organises spending using categories that belong to them alone. | `SRC-001 §6.5` | RULED |
| `R-REC-05` | A new account starts with eight categories already there, so the first entry needs no setup. | `SRC-001 §6.5` | **OPEN** — `OPEN-CAT-01` (which eight, and their colours) |
| `R-REC-06` | Removing a category never removes the spending recorded against it. History survives reorganisation. | `SRC-001 §7.2` | RULED |
| `R-REC-07` | A person can attach a receipt image to an entry. | `SRC-001 §7.5` | RULED — see E4 |

### E3 — Understanding where the money went

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-UND-01` | A person sees what they spent over a period they choose. | `SRC-001 §7.4`, `§9.2` | RULED |
| `R-UND-02` | Common periods are one click; any other period can be set by hand. | `SRC-001 §9.2` | **OPEN** — `OPEN-CHIPS-01` (what each preset means) |
| `R-UND-03` | For any period: the total, how many entries, the daily average, the split by category, and the day-by-day pattern including days with no spending. | `SRC-001 §7.4` | RULED |
| `R-UND-04` | The daily average is the total divided by the days elapsed, capped at today. | `SW-ADR-010`, `SW-ADR-053` | RULED |
| `R-UND-05` | The category split **is** the filter — one object, not a chart beside a control. | `SRC-001 §9.2` | RULED |
| `R-UND-06` | The whole view arrives in one request, not five. | `SRC-001 §7.4` | RULED |
| `R-UND-07` | Whether filtering by category also re-scopes the headline figures. | `SRC-001 §9.2` | **OPEN** — `OPEN-RIBBON-01` |
| `R-UND-08` | Whose calendar decides what "today" and "this month" mean. | — | **OPEN** — `OPEN-TZ-01` |

### E4 — Receipts

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-RCP-01` | A person can attach an image or PDF of a receipt to an entry, and view it later. | `SRC-001 §7.5`, `§8.1` | RULED |
| `R-RCP-02` | Only the person who owns the entry can ever reach its receipt — including administrators. | `SRC-001 §8.3`, `§4.5`, `SW-ADR-074` | RULED |
| `R-RCP-03` | Receipts are optional. With storage unconfigured the product still works, and says so rather than failing. | `SRC-001 §8.4` | RULED |
| `R-RCP-04` | A receipt file that is too large, or of the wrong kind, is refused before it costs anything. | `SRC-001 §8.3`, `SW-ADR-047` | RULED |

### E5 — Keeping accounts working

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-ADM-01` | An administrator can find any account. | `SRC-001 §7.6` | RULED |
| `R-ADM-02` | An administrator can see who is currently signed in. | `SRC-001 §7.6` | RULED |
| `R-ADM-03` | An administrator can end someone's sessions immediately. | `SRC-001 §7.6` | RULED |
| `R-ADM-04` | An administrator can issue a password reset. Doing so ends every session that person had — a reset that leaves the old session working is not a reset. | `SRC-001 §7.6`, `§5.5` | RULED |
| `R-ADM-05` | An administrator can deactivate and reactivate an account. | `SRC-001 §7.6` | **OPEN** — `OPEN-DEACT-01` (what deactivation actually does) |
| `R-ADM-06` | An administrator can promote or demote another administrator. | `SRC-001 §7.6` | RULED |
| `R-ADM-07` | **The product can never be left with no administrator.** No sequence of permitted actions may reach that state. | `SRC-001 §4.4` | **OPEN** — `OPEN-ADMINSELF-01` (the guard covers demotion only; deactivation reaches the same dead end) |
| `R-ADM-08` | An administrator can read the record of administrative actions. | `SRC-001 §7.6` | RULED |
| `R-ADM-09` | Where a person redeems the reset code they were given. | `SRC-001 §7.1` | **OPEN** — `OPEN-RESETUI-01` (no screen for it exists) |

### E6 — Privacy and the record

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-PRV-01` | **A person's spending is visible only to them.** This is the product's first sentence and its central promise. | `SRC-001 §1`, `§10.2` | RULED |
| `R-PRV-02` | **An administrator can never see another person's amounts or descriptions.** Counts and dates only. Changing this requires a deliberate decision, not a code change. | `SRC-001 §4.5` | RULED |
| `R-PRV-03` | Every administrative action is recorded, permanently, at the moment it happens. If the record cannot be written, the action does not happen. | `SRC-001 §10.8` | RULED |
| `R-PRV-04` | The record outlives the account it describes. Deleting a person never deletes the history of what was done to their account. | `SRC-001 §6.9` | RULED |
| `R-PRV-05` | What the record may contain, and whether merely *looking* is recorded. | `SRC-001 §6.7` | **OPEN** — `OPEN-AUDIT-01` |
| `R-PRV-06` | Whether an administrator sees another person's IP address and device. | `SRC-001 §7.6` | **OPEN** — `OPEN-SESSFIELDS-01` |

### E7 — Running it

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-OPS-01` | The product ships as one thing and deploys in one step. | `SRC-001 §2.4`, `SW-ADR-020` | RULED |
| `R-OPS-02` | The client builds and operates all infrastructure by hand, deliberately, to learn it. The build session creates nothing in AWS. | `SW-ADR-005`, `SRC-002 §6` | RULED |
| `R-OPS-03` | **Nothing paid.** The product runs inside the AWS free tier or it does not run. | `SW-ADR-014`, `SRC-002 §15` | RULED |
| `R-OPS-04` | The code does not become one giant file after two months. Its structure is a stated requirement, not a preference. | `SRC-001 §1`, `§3.4` | RULED |

---

## §5 — Non-functional requirements

| ID | Requirement | Source |
|---|---|---|
| `N-ISO-01` | **Isolation is enforced twice** — once by the application, once by the database. A check in only one place is the failure this product cannot survive. | `SW-ADR-018`, `SW-ADR-041` |
| `N-ISO-02` | The isolation guarantee is **watched failing** before it is trusted: the protection is switched off on purpose, the denial test observed going red, then restored and the restoration verified. | `CONSTITUTION.md` Art IV.4 |
| `N-MON-01` | Money is never held as a decimal fraction at any point. An app whose entire job is adding numbers up cannot drift. | `SRC-001 §6.1`, `§10.1` |
| `N-SEC-01` | Passwords are never recoverable, only replaceable. Response timing never reveals whether an address has an account. | `SRC-001 §10.5` |
| `N-SEC-02` | A person's session can be ended by someone else, immediately, and that must actually take effect. | `SRC-001 §5.4` |
| `N-AVL-01` | **Every deploy is a visible outage.** One instance, one port — the replacement cannot start until the incumbent stops. | `OPEN-DEPLOY-01` *(reasoned, not observed)* |
| `N-SEC-03` | **The deployed environment has no TLS.** `SW-ADR-014` removed the load balancer that would have terminated it, so a login travels in clear. That environment is **never called production in any document**, and this is recorded as an accepted weakness rather than defaulted into. | `SW-ADR-014` |
| `N-OPS-01` | A missing required setting stops the product from starting. It never starts degraded and silent. | `CONSTITUTION.md` Art VIII.6 |

---

## §6 — What is deliberately not built, and why

| Not built | Because |
|---|---|
| Native mobile app | Website only `[SRC: SRC-001 §12.1]` |
| Reading bank SMS | Browsers cannot reach a message inbox at all `[SRC: SRC-001 §12.2]` |
| Bank / Account Aggregator integration | Requires an RBI, SEBI, IRDAI or PFRDA licence the client does not hold `[SRC: SRC-001 §12.3]` |
| Google Pay / Blinkit import | Neither hands transaction data to third parties `[SRC: SRC-001 §12.4]` |
| Self-service password reset | No email exists in the stack, so a token has no delivery route `[SRC: SW-ADR-012]` |
| Deleting a person | Specified as a cascade, but no role is granted it and no screen offers it `[SRC: OPEN-USERDEL-01]` |
| Changing your own email or password | No such capability appears in `SRC-001 §7.1` `[SRC: OPEN-USEREDIT-01]` |
| Multi-currency | INR only in v1 `[SRC: SW-ADR-013]` |

---

## §7 — Open decisions

**This document does not duplicate the register.** The authority is `CONSTITUTION.md` Article X,
which carries 37 open rows with a class, an owner and a recommendation each.

Nine of them are referenced above as the status of a specific requirement. **Two block work that
cannot start without them:**

- **`OPEN-CAT-01`** — which eight categories are seeded, and their colours. `R-REC-05` cannot be
  specified, and the day-one fixture cannot be built, until this is answered. It is a
  one-message question.
- **`OPEN-NAME-01`** — until a named human signs `CONSTITUTION.md`, this document and all 90 ADRs
  are formally ungoverned.

---

## §8 — Colophon

Every requirement above traces to `SRC-001`, `SRC-002` or an `APPROVED` ADR. Nothing was invented:
where the sources did not settle a question, this document says `OPEN` and names the register row
rather than filling the gap with something reasonable.

**This document is a view, not a source.** The `03 PRD` is derived from it and must cover every
`RULED` row here — no gap, and no requirement that does not trace back to one of these ids.
