# SpendWise — Business Requirements Document

| Field | Value |
|---|---|
| Version | **v0.2-draft** (v0.1 + the 2026-08-05 adversarial review — 28 findings, 3 critical, all addressed) |
| Decision status | **NOT_DECIDED** (fail-closed — binds nothing until ratified) |
| Release status | NOT_RELEASED |
| Drafted | 2026-08-05 from `SRC-001`, `SRC-002`, and the **70 currently APPROVED** records in `docs/01 ADR/` |
| Governed by | `spendwise-constitution@0.1.0` — **UNADOPTED**, see `OPEN-NAME-01` |

> **v0.1 failed its review.** It cited two withdrawn ADRs as live authority for the product's
> central security promise, closed two reserved decisions the register says only the client may
> close, and omitted `SRC-001 §9.4` — accessibility, phone width and visual identity — entirely.
> The findings and their disposition are in `PROGRESS.md`. This version is the repair.

---

## §1 — Reading rules and provenance grammar

**Every requirement carries a `[SRC:]` tag.** No tag means `ASSUMED`, and an `ASSUMED` statement is
inference — it can never harden into a `MUST` (`CONSTITUTION.md` Art II.5).

| Status | Meaning |
|---|---|
| `RULED` | decided, with a citation to a **currently APPROVED** record |
| `PROVISIONAL` | written down and buildable, but a ruling it depends on is still outstanding |
| `OPEN` | genuinely unruled. **Escalate, never invent.** |

**Citations are checked against the ledger, not against plausibility.** `docs/01 ADR/` holds 90
records, of which **70 are APPROVED and 20 are superseded, withdrawn or retired**. A superseded
record is not authority. This document cites only live records; where a superseding record changed
the substance, the change is carried here rather than the original.

**This document is business intent.** No technology, no schema, no endpoints. Where a mechanism is
unavoidable to state the *outcome*, it is named as a consequence and the mechanism itself belongs
in `03 PRD`.

**On conflict** (Art II.1): raw `SRC-001` → a client ruling → an `APPROVED` ADR → this document.
Stricter always wins.

---

## §2 — Scope and envelope

**In scope.** `SRC-001` §1–§11 as corrected by errata `E-1`…`E-10`, plus the **70 currently
APPROVED and RELEASED** records in `docs/01 ADR/`, per the ledger. The 20 superseded/withdrawn
records are history, not envelope — notably `SW-ADR-025` (timezone, withdrawn for exceeding
authority) and `SW-ADR-042` (an RLS waiver returned to the client).

**Hard exclusions** — MUST NOT enter scope `[SRC: SRC-001 §12]`: no native mobile app · no reading
bank SMS · no Account Aggregator or bank API integration · nothing pulled from Google Pay or
Blinkit. Each carries a stated reason: a browser cannot reach a message inbox, and India's AA
framework requires a licence the client does not hold.

**Deferred, not cancelled** `[SRC: SRC-001 §14]`: bank-statement CSV import · a web app manifest ·
note autocomplete · **the expense-edit screen** (the capability exists; the screen does not) ·
per-category budgets.

**Removed from scope after `SRC-001` was written:** self-service password reset
`[SRC: SW-ADR-012]` — no email exists anywhere in the stack, so a token would have no delivery
route. Recovery is administrator-issued.

**Win condition** `[SRC: CONSTITUTION.md Art I.5]`. A person signs up, logs an expense, sees a
correct dashboard; **a second person can neither read, alter, nor delete** the first person's
money, proven at the database layer; an administrator can reset a password and force a sign-out;
it runs on AWS from a container the client deployed by hand. Past that line is fast-follow.

---

## §3 — Who this is for

| Persona | What they are trying to do |
|---|---|
| **Person** (`user`) | Record what they spend without friction, and understand where it went. The only persona whose goals the product actually serves. |
| **Administrator** (`admin`) | Keep accounts working. Exists for **one stated reason**: "I need someone to be able to reset a password when a user locks themselves out" `[SRC: SRC-001 §1]`. |

An administrator is also a person, with their own spending `[SRC: SRC-001 §4.2]`.

**The administrator is deliberately not powerful.** They manage *accounts* and cannot see *money* —
a stated product value, not an oversight (`R-PRV-02`).

> **Note on the stated reason.** `R-ACC-08` records that nothing in the sources can actually
> *produce* a locked-out account. The persona's justification currently rests on a state the
> product cannot enter.

---

## §4 — Business requirements

### E1 — Accounts and access

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-ACC-01` | A person can create their own account and start using the product immediately. | `SRC-001 §1`, `§7.1` | RULED |
| `R-ACC-02` | A returning person can sign back in. | `SRC-001 §7.1` | RULED |
| `R-ACC-03` | Signing out genuinely ends the session — it does not merely hide it. | `SRC-001 §5.4` | RULED |
| `R-ACC-04` | The product knows who is currently signed in, and can end any session on demand. | `SRC-001 §5.2`, `§5.3` | RULED |
| `R-ACC-05` | A person who cannot get in is recovered by an administrator, out of band. No self-service route exists. | `SW-ADR-012` | RULED |
| `R-ACC-06` | The first account created **in an empty database** becomes the administrator, and only a nominated address may claim it. If no administrator exists and none is nominated, **the product refuses to start** rather than opening the claim to whoever arrives first. | `SRC-001 §4.4`, `SW-ADR-021`, `SW-ADR-049` | RULED |
| `R-ACC-07` | How long a person stays signed in before being asked again. | `SRC-001 §5` | **OPEN** — `OPEN-SESSION-01` |
| `R-ACC-08` | Whether repeated failed sign-ins are recorded, and whether an account locks. **Nothing in the sources can currently produce the locked-out state that justifies the administrator persona**, and a sustained attack would leave no trace. | `SRC-001 §1` | **OPEN** — `OPEN-LOCKOUT-01` |
| `R-ACC-09` | Whether creating an account reveals that an address is already registered. Sign-in deliberately hides this; registration would give it away. | `SRC-001 §10.5` | **OPEN** — `OPEN-ENUM-01` |
| `R-ACC-10` | What makes a password acceptable. | `SRC-001 §10.10` | **OPEN** — `OPEN-PWPOLICY-01` |

### E2 — Recording what was spent

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-REC-01` | A person records a single act of spending: how much, when, optionally what it was for, and optionally which category. **An amount is always greater than zero — the product records spending, never refunds, credits, or corrections by negative entry.** | `SRC-001 §6.6`, `§7.3` | RULED |
| `R-REC-02` | Money is Indian Rupees. An amount never drifts through storage or summation — this is an app whose entire job is adding numbers up. | `SRC-001 §6.1`, `§10.1`, `SW-ADR-013` | RULED |
| `R-REC-03` | A person can correct or delete anything they recorded. | `SRC-001 §7.3` | RULED |
| `R-REC-04` | A person organises spending using categories that belong to them alone. | `SRC-001 §6.5` | RULED |
| `R-REC-05` | A new account starts with eight categories already there, so the first entry needs no setup. | `SRC-001 §6.5` | **OPEN** — `OPEN-CAT-01` |
| `R-REC-06` | Removing a category never removes the spending recorded against it. History survives reorganisation. | `SRC-001 §7.2` | RULED |
| `R-REC-07` | Whether a category can be **renamed**. `SRC-001 §7.2` lists no rename, yet justifies its own delete behaviour with "I don't want to lose history because I renamed something" — the prose assumes a capability the endpoint list omits. | `SRC-001 §7.2` | **OPEN** — `OPEN-RENAME-01` |
| `R-REC-08` | Whether a description is required, and whether an empty one is allowed. | `SRC-001 §6.6` | **OPEN** — `OPEN-DESC-01` |
| `R-REC-09` | What happens to an amount typed with more than two decimal places. The client's own words were "till .00 then round it off"; whether that means reject or round is unsettled. | `SRC-002 §14` | **OPEN** — `OPEN-DECIMALS-01` |
| `R-REC-10` | Whether spending may be dated in the future, and how far into the past. | `SRC-001 §6.6` | **OPEN** — `OPEN-FUTURE-01` |
| `R-REC-11` | Whether deleting a category or an entry asks for confirmation, and whether the blast radius is shown first. | `SRC-001 §7.2` | **OPEN** — `OPEN-DESTRUCT-01` |

### E3 — Understanding where the money went

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-UND-01` | A person sees what they spent over a period they choose. | `SRC-001 §7.4`, `§9.2` | RULED |
| `R-UND-02` | Common periods are one click; any other period can be set by hand. **What each preset means** is unsettled. | `SRC-001 §9.2` | **OPEN** — `OPEN-CHIPS-01` |
| `R-UND-03` | For any period: the total, how many entries, the daily average, the split by category, and the day-by-day pattern **including days with no spending**. | `SRC-001 §7.4` | RULED |
| `R-UND-04` | The daily average is the total divided by the days **elapsed** — `max(0, min(to, today) − from + 1)` — rounded **half-up** to the nearest minor unit, and reported as **no value at all** (not zero) when no days have elapsed. | `SW-ADR-053`, `SW-ADR-010` | **PROVISIONAL** — depends on `OPEN-TZ-01` per `SW-ADR-089` |
| `R-UND-05` | The category split **is** the filter — one object, not a chart beside a control. | `SRC-001 §9.2` | RULED |
| `R-UND-06` | The whole view arrives as one coherent result, not assembled from several. | `SRC-001 §7.4` | RULED |
| `R-UND-07` | Whether filtering by category also re-scopes the headline figures. If it does not, the page shows a total that visibly disagrees with the subtotals printed beneath it. | `SRC-001 §9.2` | **OPEN** — `OPEN-RIBBON-01` |
| `R-UND-08` | **Whose calendar decides what "today" and "this month" mean.** | `SRC-001 §7.4`, `SW-ADR-089` | **OPEN** — `OPEN-TZ-01` |
| `R-UND-09` | Whether spending with no category appears in the split. Such entries are **guaranteed to exist** — `R-REC-06` creates them — so if they are dropped, the split sums to less than the total shown above it. | `SRC-001 §7.2`, `§7.4` | **OPEN** — `OPEN-UNCAT-01` |
| `R-UND-10` | A period containing no spending shows an honest empty result, never a page of zeros that could be mistaken for a failed load. | `SW-ADR-054`, `SW-ADR-057` | RULED |
| `R-UND-11` | Money is displayed in the Indian grouping convention, and columns of figures line up. | `SRC-001 §9.4`, `SW-ADR-056` | RULED |
| `R-UND-12` | Whether the period a person may request is bounded. | `SRC-001 §9.2` | **OPEN** — `OPEN-RANGECAP-01` |

### E4 — Receipts

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-RCP-01` | A person can attach an image or PDF of a receipt to an entry, view it later, **replace it, and remove it**. | `SRC-001 §7.5`, `§8.1`, `SW-ADR-087` | RULED |
| `R-RCP-02` | Only the person who owns the entry can ever reach its receipt — **including administrators**. A receipt is the densest possible carrier of the amounts and descriptions `R-PRV-02` protects. | `SRC-001 §8.3`, `§4.5`, `SW-ADR-074` | RULED |
| `R-RCP-03` | Receipts are optional. With storage unconfigured the product still works, and says so rather than failing. | `SRC-001 §8.4` | RULED |
| `R-RCP-04` | A receipt file that is too large, or of the wrong kind, is refused before it costs anything. | `SRC-001 §8.3`, `SW-ADR-047` | RULED |
| `R-RCP-05` | What happens to a stored receipt when its entry is deleted, or when an upload is abandoned halfway. | `SRC-001 §8.1` | **OPEN** — `OPEN-S3LIFE-01` |

### E5 — Keeping accounts working

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-ADM-01` | An administrator can find any account. | `SRC-001 §7.6` | RULED |
| `R-ADM-02` | An administrator can see who is currently signed in. **"Currently" means last active within fifteen minutes, with the session not revoked.** | `SRC-001 §7.6`, `§5.3` | RULED |
| `R-ADM-03` | An administrator can end someone's sessions immediately. | `SRC-001 §7.6` | RULED |
| `R-ADM-04` | An administrator can issue a password reset. It ends every session that person had — a reset that leaves the old session working is not a reset. **The code works once and expires within an hour.** | `SRC-001 §7.6`, `§5.5`, `§10.7`, `SW-ADR-012` | RULED — but see `R-ADM-10` |
| `R-ADM-05` | An administrator can deactivate and reactivate an account. **What deactivation actually does** — refuse sign-in, end live sessions, or both — is unsettled. | `SRC-001 §7.6` | **OPEN** — `OPEN-DEACT-01` |
| `R-ADM-06` | An administrator can promote or demote another administrator. | `SRC-001 §7.6` | **OPEN in part** — see `R-ADM-10`, `R-ADM-11` |
| `R-ADM-07` | **The product can never be left with no administrator.** No sequence of permitted actions may reach that state. `SRC-001 §4.4` guards demotion only; deactivation reaches the identical dead end with no route back. | `SRC-001 §4.4` | **OPEN** — `OPEN-ADMINSELF-01` |
| `R-ADM-08` | An administrator can read the record of administrative actions. | `SRC-001 §7.6` | RULED |
| `R-ADM-09` | Where a person redeems the code they were given. **No screen for this exists in any source** — as written, the locked-out person receives a code and a dead end. | `SRC-001 §7.1` | **OPEN** — `OPEN-RESETUI-01` |
| `R-ADM-10` | **Whether an administrator may act on another administrator at all.** Issuing a reset against a peer is a complete account takeover: the code is shown to the issuer and the target is signed out in the same act. | `SRC-001 §7.6` | **OPEN** — `OPEN-ADMINSELF-01` |
| `R-ADM-11` | What happens to someone's live sessions when their role changes. A demoted administrator otherwise keeps every power until their session expires. | `SRC-001 §7.6` | **OPEN** — `OPEN-ROLECHG-01` |
| `R-ADM-12` | Whether a person can be deleted at all. `SRC-001 §6.9` specifies the cascade in careful detail, but no role is granted the power and no screen offers it. | `SRC-001 §6.9` | **OPEN** — `OPEN-USERDEL-01` (IRREVERSIBLE) |

### E6 — Privacy, authority and the record

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-PRV-01` | **A person's spending is visible only to them.** The product's first sentence and its central promise. | `SRC-001 §1`, `§10.2` | RULED |
| `R-PRV-02` | **An administrator can never see another person's amounts or descriptions.** Counts and dates only. Changing this requires a deliberate decision, not a code change. | `SRC-001 §4.5` | RULED |
| `R-PRV-03` | Every administrative action is recorded, permanently, at the moment it happens. **If the record cannot be written, the action does not happen.** | `SRC-001 §10.8` | RULED |
| `R-PRV-04` | The record outlives the account it describes. | `SRC-001 §6.9` | RULED |
| `R-PRV-05` | What the record may contain, and whether merely *looking* is recorded. | `SRC-001 §6.7` | **OPEN** — `OPEN-AUDIT-01` |
| `R-PRV-06` | Whether an administrator sees another person's IP address and device. | `SRC-001 §7.6` | **OPEN** — `OPEN-SESSFIELDS-01` |
| `R-PRV-07` | **Administrative capability is refused to anyone who does not hold it, checked on the server on every request.** Concealing it in the interface is presentation, never the control. Every "no" in the permission matrix is a requirement, not an absence. | `SRC-001 §4.2`, `§4.3`, `§9.1` | RULED |
| `R-PRV-08` | Whether a person may change their own email, display name, or password. No source grants it, so as specified the answer is no — which means changing a password requires an administrator. | `SRC-001 §7.1` | **OPEN** — `OPEN-USEREDIT-01` |

### E7 — Running it

| ID | Requirement | Source | Status |
|---|---|---|---|
| `R-OPS-01` | The product ships as one thing and deploys in one step. | `SRC-001 §2.4`, `SW-ADR-020` | RULED |
| `R-OPS-02` | The client builds and operates all infrastructure by hand, deliberately, to learn it. The build session creates nothing in AWS and gives advance notice of everything the client will need. | `SW-ADR-005`, `SRC-002 §6` | RULED |
| `R-OPS-03` | **Nothing paid.** The product runs inside the AWS free tier or it does not run. | `SW-ADR-014`, `SRC-002 §15` | RULED |
| `R-OPS-04` | The code does not become one giant file after two months. Its structure is a stated requirement, not a preference. | `SRC-001 §1`, `§3.4` | RULED |
| `R-OPS-05` | **When schema changes are applied relative to start-up.** `SW-ADR-005` and `SW-ADR-019` are both APPROVED and say opposite things; the authority order cannot separate two same-rank records. | `SRC-001 §11.6` | **OPEN** — `OPEN-MIGRATE-01` |
| `R-OPS-06` | **Whether anyone can tell the product is down.** The health endpoint exists because a load balancer would call it — and `SW-ADR-014` removed the load balancer. Nothing calls it now. | `SRC-001 §7.7` | **OPEN** — `OPEN-MONITOR-01`, `OPEN-LOGS-01` |

---

## §5 — Non-functional requirements

| ID | Requirement | Source | Status |
|---|---|---|---|
| `N-ISO-01` | **Isolation is enforced twice** — once by the application, once by the database — for a person's **spending, categories and sessions**. A check in only one place is the failure this product cannot survive. | `SW-ADR-078`, `SW-ADR-082`, `SW-ADR-071` | RULED |
| `N-ISO-02` | The isolation guarantee is **watched failing** before it is trusted: the protection is switched off on purpose, the denial observed going red, then restored and the restoration verified. The proof covers **reading, altering and deleting** — not reading alone. | `SW-ADR-078`, `CONSTITUTION.md` Art IV.4 | **PROVISIONAL** — the Constitution is UNADOPTED |
| `N-ISO-03` | **Whether the accounts table and the reset-code table may sit outside the database-layer guarantee.** Both hold pre-authentication paths that a per-person rule cannot serve; both are currently protected by the application alone. This is a waiver, and waivers are the client's. | `SW-ADR-090`, `SW-ADR-071` | **OPEN** — `OPEN-USERSRLS-01` |
| `N-MON-01` | Money is **never held as a binary floating-point number** at any point. Parsing uses exact decimal arithmetic; storage is integer minor units; formatting happens only at the moment of display. | `SRC-001 §6.1`, `§10.1` | RULED |
| `N-SEC-01` | Passwords are never recoverable, only replaceable. **At sign-in**, response timing never reveals whether an address has an account. | `SRC-001 §10.5` | RULED |
| `N-SEC-02` | A person's session can be ended by someone else, immediately, and that must actually take effect. | `SRC-001 §5.4` | RULED |
| `N-SEC-03` | **The deployed environment has no TLS.** `SW-ADR-014` removed the load balancer that would have terminated it, so credentials cross the network unprotected. That environment is **never called production in any document**, and this is an accepted, recorded weakness — not a default. | `SW-ADR-014` | RULED |
| `N-SEC-04` | Sign-in and password reset are rate-limited harder than everything else. **The numbers are unsettled**, and without numbers no acceptance criterion here can be binary. | `SRC-001 §10.9` | **OPEN** — `OPEN-RATE-01` |
| `N-AVL-01` | **Every deploy is a visible outage.** *(Reasoned, not observed — the build session has never run this.)* | `SW-ADR-005` | **OPEN** — `OPEN-DEPLOY-01` |
| `N-OPS-01` | A missing required setting stops the product from starting. It never starts degraded and silent. | `CONSTITUTION.md` Art VIII.6 | **PROVISIONAL** — the Constitution is UNADOPTED |
| `N-UX-01` | **The product works down to phone width.** `SRC-001 §12.1` excludes a native app, so the phone-width web experience *is* the entire mobile product. | `SRC-001 §9.4` | RULED |
| `N-UX-02` | The product has a deliberate visual identity — paper and pine green, a serif for display, a sans for body, a monospace for every number, with figures that align in columns. Not the default blue dashboard. | `SRC-001 §9.4` | RULED |
| `N-A11Y-01` | Keyboard focus is visible and reduced-motion preferences are respected. **The category split is the primary filter control and currently has no keyboard or screen-reader equivalent at all** — which must be settled *before* the design system is written, not after. | `SRC-001 §9.4` | **OPEN** — `OPEN-A11Y-01` |

---

## §6 — What no source asked for

Only things a **source excluded**. Anything the register is still asking about lives in §4 as an
`OPEN` requirement — that was v0.1's third critical defect.

| Not built | Because |
|---|---|
| Native mobile app | Website only `[SRC: SRC-001 §12.1]` |
| Reading bank SMS | Browsers cannot reach a message inbox `[SRC: SRC-001 §12.2]` |
| Bank / Account Aggregator integration | Requires a licence the client does not hold `[SRC: SRC-001 §12.3]` |
| Google Pay / Blinkit import | Neither hands transaction data to third parties `[SRC: SRC-001 §12.4]` |
| Self-service password reset | No email exists in the stack `[SRC: SW-ADR-012, SRC-001 erratum E-3]` |
| Multi-currency | INR only in v1 `[SRC: SW-ADR-013, SRC-001 erratum E-7]` |

---

## §7 — Open decisions

The authority is `CONSTITUTION.md` **Article X**, which carries **37 rows**. This document does not
duplicate it. **Twenty-six** rows are referenced above as the status of a specific requirement.

**Five are listed as blocking** in Article X.1:

| | |
|---|---|
| `OPEN-NAME-01` | Until a named human signs the Constitution, this document and all 90 ADRs are formally ungoverned. |
| `OPEN-CAT-01` | Which eight categories are seeded, and their colours. Blocks `R-REC-05` and the day-one fixture. **A one-message question.** |
| `OPEN-MIGRATE-01` | Two of the client's own APPROVED ADRs contradict each other. `R-OPS-05`. |
| `OPEN-CREDS-01` | Where database credentials live. Reserved: secrets. |
| `OPEN-MODEL-01` | What may enter an AI model. Reserved: legal. |

Rows not referenced here are technical and belong to `03 PRD` or `06 DataModel`.

---

## §8 — Colophon: what this document actually rests on

**Stated plainly, because v0.1's colophon claimed more than was true and that single sentence
certified its own defects out of existence.**

- Every functional requirement traces to `SRC-001`, `SRC-002`, or a **currently APPROVED** ADR.
  Citations were reconciled against the ledger's `decision_status` column on 2026-08-05; v0.1 was
  not, and cited two withdrawn records as authority for the product's central security promise.
- **Three requirements rest on `CONSTITUTION.md`, which is UNADOPTED** — `N-ISO-02` and `N-OPS-01`
  are marked `PROVISIONAL` for that reason, and the win condition in §2 inherits the same caveat.
- **`N-AVL-01` is reasoned, not observed.** The build session has never run a deployment and, under
  `SW-ADR-005`, never will.
- **Twenty-six requirements are `OPEN` or `PROVISIONAL`.** That is not incompleteness — it is the
  register refusing to let the build session answer questions reserved to the client.
- `CONSTITUTION.md` is itself stale about its own contents: it says 22 ADRs where there are 90, and
  seven errata where there are ten. Raised against that document; this one does not inherit the
  wrong figures.

**This document is a view, not a source.** The `03 PRD` is derived from it and must cover every
`RULED` and `PROVISIONAL` row — no gap — with no requirement that fails to trace back to an id here.
