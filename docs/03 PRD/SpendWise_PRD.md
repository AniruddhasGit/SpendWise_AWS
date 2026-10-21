# SpendWise — Product Requirements Document

| Field | Value |
|---|---|
| Version | v0.1-draft |
| Decision status | **NOT_DECIDED** (fail-closed) |
| Release status | NOT_RELEASED |
| Drafted | 2026-08-05 from `SRC-001`, `SRC-002`, `02 BRD` v0.3, `05 B DesignSystem`, and the 135 records in `docs/01 ADR/` |
| Governed by | `spendwise-constitution@0.1.0` — **UNADOPTED**, see `OPEN-NAME-01` |

> **This is the document the code is written from.** Every `P-` row states behaviour precisely
> enough that a stranger could build it without inventing anything. Where a source did not
> settle something, this document cites the ruling that did — it never fills the gap itself.

---

## §1 — Reading rules

Every `P-` row carries **two** references: a `[SRC:]` tag (where the requirement came from) and
a **BRD row** (which business requirement it satisfies). A row missing either is a defect:
no `[SRC:]` means invented, no BRD row means scope creep.

Citations resolve against **currently APPROVED** records only. 24 of the 160 ADRs are
superseded or withdrawn and are not authority.

**Status:** `RULED` (decided, cited) · `PROVISIONAL` (buildable, a dependency outstanding) ·
`OPEN` (escalate, never invent).

**All 38 Article X rows were adjudicated by Fable 5 on 2026-08-05** (`SW-ADR-091`…`128`), so
this document has no `OPEN` behaviour. Two rows remain client-only — the ratification signature
and legal sub-processor posture — and neither gates any behaviour specified here.

---

## §2 — Scope

Carried unchanged from `02 BRD` §2. Nothing is added here. The hard exclusions, the deferrals,
and the win condition all stand as written there.

**Out of scope for this document specifically:** database schema (that is `06 DataModel`), the
build order (that is `05 Bible`), and infrastructure (that is the client's, per `SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13)).

---

## §3 — Personas, roles and surfaces

### §3.1 — Roles

Two, stored as a column on the user record: `user` and `admin` `[SRC: SRC-001 §4.1]`.
Written once as `get_current_user` and `require_admin`, applied as a router-level dependency —
**one place, never a check copy-pasted per handler** `[SRC: SRC-001 §4.3]`.

**The role is re-read from the user record on every request, never trusted from a token claim**
`[SRC: SW-ADR-101]`. A demoted administrator loses every power on their very next request.

### §3.2 — Surface and route inventory

| Route | Surface | Who | Notes |
|---|---|---|---|
| `/signin` | Sign in · Create account · **Redeem reset code** | anonymous | one page, three modes `[SRC: SRC-001 §9.1, SW-ADR-110]` |
| `/` | Dashboard | any signed-in | `from`, `to`, `category` **(the browser URL — the API parameter is `category_id`, plus `uncategorised`; the dashboard route is not the API route)` in the query string `[SRC: SW-ADR-075]` |
| `/admin` | Account administration | `admin` only | server-enforced, not UI-hidden `[SRC: SRC-001 §9.1]` |
| `/admin/audit` | The administrative record | `admin` only | a sub-view; `§9.3`'s "Plus the audit log" `[SRC: SW-ADR-110]` |
| *(any unmatched)* | Not-found screen | any | the SPA catch-all serves `index.html`; the client router shows a real 404 `[SRC: SW-ADR-075]` |
| `/api/*` *(unmatched)* | JSON 404 | — | **never falls through to the SPA** — a typo'd API path must not return HTML with a 200 `[SRC: SW-ADR-075]` |

A non-administrator reaching `/admin` gets an explicit no-access screen, **not** the admin shell
failing request by request `[SRC: SW-ADR-075]`.

---

## §4 — Specifications

### E1 — Accounts and access

**`P-ACC-01` Register** — BRD `R-ACC-01` · `[SRC: SRC-001 §7.1]`
Anonymous. Input: email, password, display name. Creates the account, seeds the eight
categories of `P-REC-05`, signs the person in, returns them to the dashboard.
· Password: **minimum 12 characters, maximum 72 bytes UTF-8**, no composition rules
`[SRC: SW-ADR-103]`. The 72 is a bcrypt property, documented as such, never raised.
· Email is stored as typed and compared case-insensitively `[SRC: SW-ADR-027]`.
· **Duplicate email → 409, "An account with this email already exists."** `[SRC: SW-ADR-102]`
This deliberately reveals existence at registration; the sign-in path stays dark (`P-ACC-03`).
· Rate limited: 5/min and 20/day per IP `[SRC: SW-ADR-128]`.
**Exceptions:** password too short → 422 · password over 72 bytes → 422 · malformed email → 422 ·
missing display name → 422.

**`P-ACC-02` First administrator** — BRD `R-ACC-06` · `[SRC: SRC-001 §4.4, SW-ADR-021, SW-ADR-049]`
The bootstrap claim is evaluated **only when the administrator count is zero**, and only for the
address in `BOOTSTRAP_ADMIN_EMAIL`, matched case-insensitively. If no administrator exists and
the variable is unset, **the application refuses to start** — a loud five-second failure rather
than a silent permanent lockout. After the first, only an existing administrator promotes.

**`P-ACC-03` Sign in** — BRD `R-ACC-02` · `[SRC: SRC-001 §7.1, §10.5]`
Input: email, password. On success: a session record is created, a token carrying its id as
`jti` is set in an **httpOnly, SameSite=Lax** cookie, `Secure` driven by an environment variable
`[SRC: SRC-001 §10.4, SW-ADR-014]`.
· **The bcrypt comparison runs even when the email is unknown**, against a fixed dummy hash, so
response timing reveals nothing `[SRC: SRC-001 §10.5]`.
· bcrypt cost 12, executed **off the event loop** `[SRC: SRC-001 §10.5]`.
· **Every failure returns the same generic 401** — wrong password, unknown email, and
deactivated account are indistinguishable `[SRC: SW-ADR-100]`.
· Every failed attempt emits one structured WARN line: normalized email, source IP, user agent,
request id. **No account lockout exists** `[SRC: SW-ADR-104]`.
· Rate limited: 10/min per IP **and** 10/min per email `[SRC: SW-ADR-128]`.
· On success the session prune of `P-OPS-04` runs.

**`P-ACC-04` Session validity** — BRD `R-ACC-04`, `R-ACC-07` · `[SRC: SRC-001 §5.2, SW-ADR-099]`
Every authenticated request resolves the token's `jti` to a session record and requires: the
record exists · `revoked_at` is null · now ≤ `expires_at` · idle since `last_seen_at` is within
the role's window.
· **Absolute cap 30 days. Idle: 14 days for `user`, 30 minutes for `admin`.**
· `last_seen_at` is bumped at most once a minute, decided by comparing the timestamp on the
record **already fetched** — no in-process state, so it behaves identically across workers
`[SRC: SW-ADR-022]`.
· Failure → 401 with code `SESSION_INVALID`.

**`P-ACC-05` Sign out** — BRD `R-ACC-03` · `[SRC: SRC-001 §5.4]`
Sets `revoked_at`, clears the cookie. **Replaying the old cookie is rejected** — the session
record is the authority, not the token's signature alone.

**`P-ACC-06` Current user** — BRD `R-ACC-04` · `[SRC: SRC-001 §7.1]`
Returns id, email, display name, role, and `receipts_enabled` so the client can hide the receipt
control when storage is unconfigured rather than letting it fail `[SRC: SRC-001 §8.4]`.

**`P-ACC-07` Redeem a reset code** — BRD `R-ADM-09` · `[SRC: SW-ADR-110]`
Anonymous, third mode of `/signin`. Input: email, code, new password.
· The code is hashed and matched; single use; one-hour expiry `[SRC: SRC-001 §10.7]`.
· On success **every session of that person is revoked in the same transaction**
`[SRC: SRC-001 §5.5]`, the password is replaced, and the person is returned to sign-in with
"Password updated — sign in with your new password." **No auto-login.**
· **Four distinct outcomes**, each with its own message `[SRC: SW-ADR-110]`:
invalid → "This reset code is not recognised." · already used → "This reset code has already
been used — ask your administrator for a new one." · expired → "This reset code has expired —
ask your administrator for a new one." · success as above.
· Rate limited: 6/min per IP `[SRC: SW-ADR-128]`.

### E2 — Recording spending

**`P-REC-01` Create an expense** — BRD `R-REC-01` · `[SRC: SRC-001 §7.3]`
Input: amount, date, optional description, optional category.
· **Amount** is parsed as an exact decimal at the boundary and converted to integer paise in a
validator. **More than two decimal places → 422, "Amount must have at most two decimal
places."** — never rounded `[SRC: SW-ADR-112]`. Must be **> 0** `[SRC: SRC-001 §6.6]` and
≤ 10¹² paise `[SRC: SW-ADR-079]`.
· **Date** must satisfy `today − 10 years ≤ spent_on ≤ today + 1 year`, evaluated in
**Asia/Kolkata** `[SRC: SW-ADR-096, SW-ADR-111]`. Never defaulted server-side — the browser
always sends it.
· **Description** optional, ≤ 500 characters; empty or whitespace-only is **normalized to null**
so "no description" has exactly one representation `[SRC: SW-ADR-115]`.
· **Category**, if given, must belong to the caller — enforced by the database, because foreign-key
checks bypass row security entirely `[SRC: SW-ADR-072]`.
· The currency is snapshotted onto the row at write time `[SRC: SW-ADR-013]`.
· Server-derived fields are server-derived: a forged owner id, a forged total or a forged record
id in the request body is ignored.

**`P-REC-02` List expenses** — BRD `R-REC-01` · `[SRC: SRC-001 §7.3, SW-ADR-038]`
Filters: date range (inclusive both ends `[SRC: SW-ADR-085]`), optional category, and an
explicit **uncategorised** filter. Sorted `spent_on DESC, created_at DESC, id DESC` — the id
tiebreak is what makes the order total, without which pagination duplicates and skips rows.
Limit default 50, maximum 200. Returns `{items, total, limit, offset}`.

**`P-REC-03` Update an expense** — BRD `R-REC-03` · `[SRC: SRC-001 §7.3]`
Mutable: amount, date, description, category. Not mutable: owner, id, timestamps. Same
validation as `P-REC-01`. *(The endpoint exists in v1; the screen does not — `SRC-001 §14`.)*

**`P-REC-04` Delete an expense** — BRD `R-REC-03` · `[SRC: SRC-001 §7.3]`
Confirms first, naming the amount and date, and warning when a receipt will go with it
`[SRC: SW-ADR-119]`. Its receipt object is deleted **after** the row commits, best-effort
`[SRC: SW-ADR-087]`.

**`P-REC-05` Categories** — BRD `R-REC-04`, `R-REC-05`, `R-REC-06`, `R-REC-07` ·
`[SRC: SRC-001 §6.5, §7.2, SW-ADR-092, SW-ADR-114]`
List, create, **rename and recolour**, delete. Names are unique per person, case-insensitively
`[SRC: SW-ADR-033]`; a conflict returns 409.
· **Eight seeded at account creation**, in order: Groceries · Food & Dining · Transport ·
Rent & Utilities · Health · Entertainment · Shopping · Other, with the hex values in
`05 B DesignSystem` §2.2 `[SRC: SW-ADR-092]`.
· **Deleting a category nulls `category_id` on every expense that used it and deletes nothing
else** `[SRC: SRC-001 §7.2]`. The confirm names the count: *"Delete Groceries? 47 expenses will
become uncategorised."* `[SRC: SW-ADR-119]`
· **Renaming never touches expenses** — the link is by id, so history follows the category
`[SRC: SW-ADR-114]`.

### E3 — Understanding spending

**`P-UND-01` The summary** — BRD `R-UND-01`, `R-UND-03`, `R-UND-06` · `[SRC: SRC-001 §7.4]`
One request returns everything the dashboard needs: total, entry count, daily average, the
breakdown by category, and **one row per calendar day including days with no spending**.
Optional `category_id` re-scopes everything except the breakdown itself.

**`P-UND-02` The daily average** — BRD `R-UND-04` · `[SRC: SW-ADR-053, SW-ADR-010]`

```
elapsed = max(0, min(to, today) − from + 1)        # today in Asia/Kolkata
average = round_half_up(total_paise / elapsed)     # integer paise
average = null  when elapsed = 0                   # rendered as "—", never as 0
```

**The agreed acceptance value:** range 1–31 Aug with today the 5th; expenses ₹1,250.00 (Aug 1),
₹340.50 (Aug 3), ₹2,100.00 (Aug 3), ₹99.99 (Aug 5). Total 379,049 paise, count 4, elapsed 5,
**average = 75,810 paise**. The application computes this from seeded rows; a fixture asserting
on itself does not satisfy the gate `[SRC: CONSTITUTION.md Art IX.4]`.

**`P-UND-03` Period presets** — BRD `R-UND-02` · `[SRC: SW-ADR-108]`
All boundaries in Asia/Kolkata. **This week** = Monday 00:00 of the current ISO week through
Sunday · **This month** = the 1st through the last day of the current month · **Last month** =
the whole previous month · **This year** = 1 Jan through 31 Dec. Plus custom dates.
The browser resolves the preset into explicit `from`/`to`; **the server never guesses "this
month"**.

**`P-UND-04` Range validation** — BRD `R-UND-12` · `[SRC: SW-ADR-118]`
`from > to` → 422 · span > **400 days** → 422 naming the cap · `from < 2000-01-01` → 422.

**`P-UND-05` The category breakdown** — BRD `R-UND-09` · `[SRC: SW-ADR-131]`
Returns `category_id`, name, colour, total, and percentage. Names come from the categories
service, not a join — the expenses repository returns ids and totals, the **service** stitches
`[SRC: SW-ADR-017]`. One request for the browser; the module seam stays intact.
· **Uncategorised is a real bucket**: id null, label "Uncategorised", colour `#948c87`, **always
ordered last** regardless of size, clickable to filter `category_id IS NULL`.
· **Invariant, asserted in tests: the breakdown sums exactly to the headline total.**

**`P-UND-06` Empty range** — BRD `R-UND-10` · `[SRC: SW-ADR-054]`
total 0, count 0, breakdown `[]`, and the **full day series of zero-valued days**.
**The average is `null` only when `days_elapsed` is 0** — a wholly future range `[SRC: SW-ADR-053]`. An empty range that HAS elapsed (a new account opening 1–31 August on the
5th — the first screen every new user sees) has `days_elapsed: 5` and therefore
`daily_average_paise: 0`, which is the truth: five days elapsed, nothing spent.
*(Corrected 2026-08-05. This sentence previously read "average null" beside "full day series",
and those cannot both hold — a full series means time has elapsed. Built as written, the first
screen renders ₹0.00 where `P-UND-02` requires an em-dash. Found by the fourth uncoached
slice, contradiction C1.)*
The client shows a distinct first-run state for a brand-new account and a distinct
"nothing in this period" state for an empty filter — **and never renders zeros for a failed
request**, which in a money app is indistinguishable from a true zero `[SRC: SW-ADR-057]`.

**`P-UND-07` Money formatting** — BRD `R-UND-11` · `[SRC: SRC-001 §9.4, SW-ADR-157]`
Every amount renders through **one shared formatter** in US dollars, `en-US` grouping —
$1,234,567.89 (the owner, 2026-10-20; `SW-ADR-056`'s rupees and lakh grouping are superseded).
Numbers use tabular figures so columns align. No component formats money itself.

### E4 — Receipts

**`P-RCP-01` Upload** — BRD `R-RCP-01`, `R-RCP-04` · `[SRC: SRC-001 §8, SW-ADR-047, SW-ADR-123]`
Three steps. (1) The browser requests an upload authorisation; the server returns a **presigned
POST with a policy asserting a content-length range and an allowed content type** — a bare
presigned PUT enforces neither. (2) The browser uploads straight to storage, targeting
`staging/{user_id}/{uuid}.{ext}` — the file never passes through the container. (3) The browser
tells the server the key; the server verifies the staging prefix belongs to the caller, copies
to `receipts/{user_id}/{expense_id}/{uuid}.{ext}`, deletes the staging object, and sets
`receipt_key`.
· Allowed: JPG, PNG, WEBP, PDF. Cap 10 MB. Objects carry `Content-Disposition: attachment` and a
safe content type so a stored HTML payload cannot execute.
· **Abandoned uploads expire from `staging/` after one day**, via a lifecycle rule the client
creates.
· The client checks type and size **before** requesting authorisation, so a 10 MB file is not
uploaded before being refused.

**`P-RCP-02` View, replace, remove** — BRD `R-RCP-01`, `R-RCP-02` · `[SRC: SW-ADR-074, SW-ADR-087]`
Keys are **derived server-side and never accepted from the client**; view and delete resolve the
key from the owned expense record. **The receipts endpoints are reachable only by the owner** —
there is no administrative path to a receipt, because a receipt is the densest possible carrier
of the amounts and descriptions `P-PRV-02` protects. View URLs expire in five minutes.
Replacing commits the row first, then deletes the previous object best-effort.

**`P-RCP-03` Storage unconfigured** — BRD `R-RCP-03` · `[SRC: SRC-001 §8.4]`
With no bucket configured the feature switches off gracefully: `receipts_enabled` is false in
`P-ACC-06`, the control is hidden, and one WARN line at startup names the disabled feature
`[SRC: SW-ADR-060]`.

### E5 — Administration

**`P-ADM-01` List accounts** — BRD `R-ADM-01` · `[SRC: SRC-001 §7.6]`
Paginated and searchable by email and display name. Returns email, display name, role,
`is_active`, `created_at`, and last-active time. **Never any spending figure.**

**`P-ADM-02` Active sessions** — BRD `R-ADM-02` · `[SRC: SRC-001 §5.3, SW-ADR-106]`
"Currently active" = `last_seen_at` within **15 minutes** and not revoked.
Returns user, `issued_at`, `last_seen_at`, status. **IP address and user agent are stored but
never returned** — the response model physically lacks the fields.

**`P-ADM-03` Revoke sessions** — BRD `R-ADM-03` · `[SRC: SRC-001 §7.6]`
Sets `revoked_at` on every live session of the target. Allowed against another administrator —
containment, and reversible by signing back in. Confirms, naming the count.

**`P-ADM-04` Issue a reset** — BRD `R-ADM-04`, `R-ADM-10` · `[SRC: SW-ADR-012, SW-ADR-098]`
Generates a 32-byte random code, stores only its SHA-256, one-hour expiry, single use, and
**invalidates every outstanding code for that person in the same transaction**
`[SRC: SW-ADR-032]`. The plaintext is shown to the issuing administrator **once**, never logged
`[SRC: SW-ADR-063]`, and delivered out of band. Every session of the target is revoked in the
same transaction `[SRC: SRC-001 §5.5]`.
· **Refused (403) when the target is another administrator.** To reset a peer: demote first,
then reset — two deliberate, separately audited steps rather than a one-click takeover
`[SRC: SW-ADR-098]`.
· **An administrator may reset themselves** — with no self-service password change, that is the
only password-change route anyone has.

**`P-ADM-05` Deactivate / reactivate** — BRD `R-ADM-05` · `[SRC: SW-ADR-100]`
Enforced at **three** points: sign-in refused with the generic 401 · every live session revoked
in the same transaction · `get_current_user` re-checks and fails closed with
`ACCOUNT_DEACTIVATED` and "Your account has been deactivated. Contact your administrator."
Reactivation never resurrects revoked sessions.

**`P-ADM-06` Change role** — BRD `R-ADM-06`, `R-ADM-11` · `[SRC: SW-ADR-101]`
On **demotion**, every session of the target is revoked in the same transaction. On promotion,
sessions are kept and the new role takes effect on the next request via the re-read of `P-ACC-04`.

**`P-ADM-07` The last-administrator guard** — BRD `R-ADM-07` · `[SRC: SW-ADR-098]`
**Any action that would leave zero active administrators is refused with 409** — demote or
deactivate, self or other. This extends `SRC-001 §4.4`'s guard, which covered demotion only
while deactivation reached the identical dead end with no route back.

**`P-ADM-08` The audit view** — BRD `R-ADM-08` · `[SRC: SRC-001 §7.6]`
Paginated, newest first, rendered as a formatted sentence per action — never a raw JSON blob,
which nobody reads and in which a violation would be invisible.

**`P-ADM-09` Deletion does not exist** — BRD `R-ADM-12` · `[SRC: SW-ADR-107]`
There is **no** endpoint, screen, administrative power, or seed-script path that deletes a
person. The cascade semantics stay in the schema as correctness, so a future deliberate deletion
behaves exactly as `SRC-001 §6.9` specifies — but nothing in v1 can trigger it. When deletion
comes it arrives as a client-run runbook plus a superseding ADR, never as a quietly added button.

### E6 — Privacy, authority, the record

**`P-PRV-01` Per-person isolation** — BRD `R-PRV-01`, `N-ISO-01` ·
`[SRC: SRC-001 §10.2, SW-ADR-078, SW-ADR-082]`
Every query filters on the identity in the verified token, never on anything the browser sent.
**And** row-level security enforces it at the database for `expenses`, `categories` and
`sessions`, with `FORCE ROW LEVEL SECURITY` on and policies covering **every command** with both
`USING` and `WITH CHECK` — a read-only policy would let a write cross the boundary while every
stated test stayed green.
· The request-scoped identity is set with `set_config('app.user_id', :uid, true)` and a **bound
parameter** — `SET LOCAL` cannot take one, and interpolating would be the f-string-near-SQL that
`SRC-001 §10.3` forbids `[SRC: SW-ADR-082]`.
· `users` and `password_resets` sit outside row-level security, deliberately and with four
compensating controls `[SRC: SW-ADR-097]`.

**`P-PRV-02` What an administrator may see** — BRD `R-PRV-02` ·
`[SRC: SRC-001 §4.5, SW-ADR-129]`
Counts and dates. **Never amounts, never descriptions, never receipts.**

Enforced structurally, not by memory — but by the **return type of a function**, not by a policy.
A PostgreSQL row-level policy filters *rows*; it has no column dimension, so "aggregate reads
only" is not a shape a policy can have. The superseded `SW-ADR-077` tried, and what it produced
was an unqualified permissive policy that returned every column of every row to any connection
with `app.is_admin` set.

An admin reads expense activity through exactly one path:

```sql
SELECT expense_count, last_activity FROM admin_expense_stats(:target_user_id);
```

a `SECURITY DEFINER` function returning `(expense_count BIGINT, last_activity DATE)`. **An amount
cannot come back through it because there is no column for one.** No policy on `expenses` or
`categories` consults `app.is_admin`, and `app.is_admin` is never set on a request-scoped
connection `[SRC: SW-ADR-129]`.

**Per-table policy matrix** — required by `SW-ADR-043`, published here as it directed:

| Table | User policy | Admin policy | Commands | RLS |
|---|---|---|---|---|
| `expenses` | `expenses_owner` — `user_id` = request identity | **none** | `FOR ALL`, `USING` + `WITH CHECK` | `FORCE` |
| `categories` | `categories_owner` — same | **none** | `FOR ALL`, `USING` + `WITH CHECK` | `FORCE` |
| `sessions` | `sessions_owner` — same | **none**; admin revocation goes through the admin service, which does not read another person's money | `FOR ALL`, `USING` + `WITH CHECK` | `FORCE` |
| `users` | — | — | outside RLS, four compensating controls | off `[SRC: SW-ADR-097]` |
| `password_resets` | — | — | outside RLS; redeeming a code is unauthenticated by definition | off `[SRC: SW-ADR-071]` |
| `admin_audit_log` | — | append + read | `UPDATE`/`DELETE` revoked, trigger raises | off `[SRC: SW-ADR-083]` |
| `app_meta` | — | — | one row, no person-owned data | off |

**`app.is_admin` appears in no row of this table.** That is the decision, not an omission.

**`P-PRV-03` Not-yours is indistinguishable from not-found** — BRD `R-PRV-01` ·
`[SRC: SW-ADR-050]`
**404 for every not-yours-or-not-found case, on every verb.** A 403 on an existing record and a
404 on a missing one is a working oracle: walk the id space and learn which ids are real. This
is also what makes sequential integer ids safe `[SRC: SW-ADR-023]` — the two must be reversed
together or not at all.

**`P-PRV-04` The audit record** — BRD `R-PRV-03`, `R-PRV-05` · `[SRC: SRC-001 §10.8, SW-ADR-105]`
Written in the **same transaction** as the change; if the record cannot be written, the change
rolls back. **Nine action types, each with a typed detail shape**, validated before the write:
`password_reset_issued` · `sessions_revoked` · `user_deactivated` · `user_reactivated` ·
`role_changed` · `bootstrap_admin_claimed` · and three **read-audit** types with empty details:
`users_list_viewed`, `sessions_list_viewed`, `audit_log_viewed`.
**Prohibited under any type, enforced by the schemas: tokens, password material, amounts,
descriptions, receipt keys, free text.** An action type not on the list cannot be written.
The table is immutable at the database — UPDATE and DELETE are revoked and a trigger raises
`[SRC: SW-ADR-083]` — and carries **no foreign keys**, so a person can be removed without the
record following them `[SRC: SW-ADR-083]`.

**`P-PRV-05` Authorisation** — BRD `R-PRV-07` · `[SRC: SRC-001 §4.2, §4.3, §9.1]`
Every capability the permission matrix denies is refused **on the server, on every request**.
Hiding the administration link is presentation and never the control. Every "no" in the matrix
is a requirement, and each has a negative test.

**`P-PRV-06` No self-service profile or password change** — BRD `R-PRV-08` · `[SRC: SW-ADR-116]`
A person cannot change their own email, display name, or password in v1. The only password-change
route is the administrator-issued reset of `P-ADM-04` and `P-ACC-07` — **including an
administrator issuing one against themselves**, which is why `P-ADM-04` permits the self-target.
Recorded as deliberate rather than left an accident of the endpoint list.

### E7 — Operations

**`P-OPS-01` Configuration** — BRD `R-OPS-02`, `N-OPS-01` · `[SRC: SW-ADR-060]`
All settings from environment variables through a typed loader that **fails fast** — a missing
required key aborts startup. `.env.example` is the committed manifest, each line annotated
required or optional with its default. A variable whose absence *degrades* rather than aborts —
today only the storage bucket — logs one WARN naming the disabled feature.

**`P-OPS-02` Startup** — BRD `R-OPS-01` · `[SRC: SW-ADR-093, SW-ADR-081]`
In order: load settings → **assert against the catalog that the runtime database role owns no
table, is not superuser, holds no `BYPASSRLS`, and cannot disable row security** → run
migrations under `pg_advisory_xact_lock` using the **separate migration credential** → print the
current and target revision → **compare the stored fingerprint of the signing secret and, if it
changed, revoke every live session** `[SRC: SW-ADR-125]` → bind the port.
Migration failure: no retry, exit non-zero, one structured ERROR naming the revision reached
versus target `[SRC: SW-ADR-061]`.

**`P-OPS-03` Health** — BRD `R-OPS-06` · `[SRC: SRC-001 §7.7, SW-ADR-073]`
`/healthz` — no database, bodiless 200/503; the container health check calls it.
`/readyz` — checks the database, returns `{status, revision, build}` when `EXPOSE_VERSION` is
set. An unset build version reports the literal `unset` and logs a WARN `[SRC: SW-ADR-064]`.

**`P-OPS-04` Pruning** — BRD `R-OPS-02` · `[SRC: SW-ADR-122]`
At successful sign-in, bounded to 1,000 rows per table: delete sessions dead ≥ 90 days and reset
codes used or expired ≥ 90 days ago. **The audit record is never pruned.**

**`P-OPS-05` Logging** — BRD `R-OPS-06` · `[SRC: SW-ADR-062, SW-ADR-063]`
JSON lines to stdout. Required fields: timestamp, level, message, request_id, route, method,
status, duration_ms, user_id (nullable), revision. Level from `LOG_LEVEL`, default INFO;
uvicorn's loggers are reconfigured onto the same handler so the output has one shape.
**Deny-list, enforced by a filter and red-proofed by planting each value and asserting its
absence:** password, password hash, Authorization and Cookie headers, reset codes and their
hashes, presigned URL query strings, the database URL, the signing secret. Validation error
bodies are never logged verbatim.

---

## §5 — UX specification

Binds to `docs/05 B DesignSystem`. That document is authority for colour, type, spacing, motion,
component states and the accessibility floor; this section specifies **behaviour**.

### §5.1 — Sign-in page
Three modes on one page `[SRC: SRC-001 §9.1, SW-ADR-110]`: sign in · create account · redeem a
reset code. States: default · submitting (control disabled) · error (inline, beneath the field,
never a toast) · rate-limited (429 shows a countdown from `Retry-After` and disables submit
`[SRC: SW-ADR-128]`).

### §5.2 — Dashboard
Period picker as chips plus custom dates · **the category ribbon** · a small bar per day · entries
grouped by date with a per-day subtotal · the add-expense panel `[SRC: SRC-001 §9.2]`.

**The ribbon** `[SRC: SW-ADR-109, SW-ADR-117]`. Selecting a band re-scopes the total, count,
average, day bars **and** the entry list. **The ribbon itself stays whole-period** so proportions
remain visible and other bands stay reachable; the selected band is emphasised and the rest dim.
Clicking the active band again clears the filter. Interaction, focus and ARIA are specified in
the design system §5.1 — it is a real control, not a picture.

**The add-expense panel.** Enters from the right on desktop, from the bottom on phones. A real
dialog: focus trapped on open, focus restored on close, Escape closes, the background is inert,
and a dirty form confirms before discarding.
**No optimistic insertion** `[SRC: SW-ADR-058]` — the panel waits for confirmation, then the
summary is refetched. `P-UND-02`'s rule must have exactly one implementation; recomputing it in
the browser would create a drift the day-one gate cannot see. Submit disables on first click:
there is no uniqueness constraint on expenses, so a double-submit would silently double a total.

**States.** First-run (a brand-new account: no ribbon, no bars, one line of copy and a primary
"Add your first expense") · empty filter · loading (skeleton) · **error (an in-place panel with
retry that preserves the period — never zeros)** · populated.

### §5.3 — Administration
A person table with last-active and status, an active-session count, per-person actions, and the
audit view. **Every destructive action confirms, naming the blast radius** — the exact strings
are in `SW-ADR-119`. No type-the-name friction anywhere.

### §5.4 — Session ending mid-use
One response interceptor `[SRC: SW-ADR-057]`. On 401: clear client state, route to sign-in with
a reason banner, **suppress duplicate redirects** — the dashboard fires more than one request, so
a naive per-call handler would redirect twice. The in-progress add-expense draft is held in
memory.

---

## §6 — API contract

<!-- BEGIN GENERATED ROUTES -->

| Method | Path | Who | Spec | Errors |
|---|---|---|---|---|
| POST | `/api/auth/register` | anon | `P-ACC-01` | `VALIDATION_ERROR`, `EMAIL_TAKEN`, `RATE_LIMITED`, `BAD_REQUEST` |
| POST | `/api/auth/login` | anon | `P-ACC-03` | `VALIDATION_ERROR`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `RATE_LIMITED` |
| POST | `/api/auth/logout` | any | `P-ACC-05` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED` |
| GET | `/api/auth/me` | any | `P-ACC-06` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED` |
| POST | `/api/auth/reset/complete` | anon | `P-ACC-07` | `VALIDATION_ERROR`, `NOT_FOUND`, `RATE_LIMITED` |
| GET | `/api/categories` | any | `P-REC-05` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED` |
| POST | `/api/categories` | any | `P-REC-05` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR`, `CONFLICT` |
| PATCH | `/api/categories/{category_id}` | owner | `P-REC-05` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT` |
| DELETE | `/api/categories/{category_id}` | owner | `P-REC-05` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `NOT_FOUND` |
| GET | `/api/expenses` | any | `P-REC-02` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR` |
| POST | `/api/expenses` | any | `P-REC-01` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR` |
| GET | `/api/expenses/summary` | any | `P-UND-01` · `P-UND-02` · `P-UND-03` · `P-UND-04` · `P-UND-05` · `P-UND-06` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR` |
| GET | `/api/expenses/{expense_id}` | owner | `P-REC-02` · `P-PRV-03` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `NOT_FOUND` |
| PATCH | `/api/expenses/{expense_id}` | owner | `P-REC-03` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR`, `NOT_FOUND` |
| DELETE | `/api/expenses/{expense_id}` | owner | `P-REC-04` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `NOT_FOUND` |
| POST | `/api/receipts/upload-url` | any | `P-RCP-01` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR` |
| POST | `/api/receipts/attach` | owner | `P-RCP-01` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR`, `NOT_FOUND` |
| GET | `/api/receipts/{expense_id}/url` | owner | `P-RCP-02` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `NOT_FOUND` |
| DELETE | `/api/receipts/{expense_id}` | owner | `P-RCP-02` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `NOT_FOUND` |
| GET | `/api/admin/users` | admin | `P-ADM-01` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN` |
| GET | `/api/admin/sessions` | admin | `P-ADM-02` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN` |
| POST | `/api/admin/users/{user_id}/revoke-sessions` | admin | `P-ADM-03` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN`, `NOT_FOUND` |
| POST | `/api/admin/users/{user_id}/reset` | admin | `P-ADM-04` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN`, `NOT_FOUND` |
| POST | `/api/admin/users/{user_id}/active` | admin | `P-ADM-05` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR` |
| POST | `/api/admin/users/{user_id}/role` | admin | `P-ADM-06` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT` |
| GET | `/api/admin/audit` | admin | `P-ADM-08` | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN` |
| GET | `/healthz` | anon | `P-OPS-03` | — |
| GET | `/readyz` | anon | `P-OPS-03` | — |
| PATCH | `/api/auth/me` | any |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR` |
| POST | `/api/auth/password` | any |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `VALIDATION_ERROR` |
| POST | `/api/auth/deactivate` | any |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `CONFLICT` |
| DELETE | `/api/auth/me` | any |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `CONFLICT` |
| GET | `/api/auth/export` | any |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED` |
| GET | `/api/admin/overview` | admin |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN` |
| GET | `/api/admin/users/{user_id}/spending` | admin |  | `UNAUTHENTICATED`, `SESSION_INVALID`, `ACCOUNT_DEACTIVATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR` |

**35 routes** (33 under `/api/`, plus `/healthz` and `/readyz`). Generated from
`contract.json`; `consistency_check.py` fails if any path named by a Bible criterion,
a SIT case or a negative case does not resolve to a row here.

**Route notes.**

- `POST /api/expenses` — 201. A forged user_id or id in the body is discarded before validation (SW-ADR-130); a category_id that is not the caller's is refused by the composite FK and mapped to 422 field=category_id (NEG-X-11). No Location header (CV-10).
- `GET /api/expenses/summary` — MUST be registered BEFORE /api/expenses/{expense_id} or the literal `summary` is captured by the integer path parameter (CV-11).
- `GET /api/expenses/{expense_id}` — ADDED 2026-08-05 by SW-ADR-140. It was required by Bible E0-S7 AC1, SIT-E0-S7-01 and the SEV-1 case NEG-X-01, and appeared in NO contract document - PRD §6, the route map and the coverage matrix all listed only PATCH and DELETE on this path.
- `GET /api/admin/users` — Audited read: writes one admin_audit_log row per request, in the same transaction, response serialised only after COMMIT (SW-ADR-135). Primary-only, never a replica or a cache.
- `GET /api/admin/sessions` — Audited read (SW-ADR-135). No ip, no user_agent (SW-ADR-106).
- `GET /api/admin/audit` — Audited read (SW-ADR-135).
- `PATCH /api/auth/me` — SW-ADR-148 C: changes the display name and NOTHING else. Email is absent from ProfileUpdate deliberately - it is the identity the unique index is built on and SW-ADR-012 records there is no email in this stack to verify a new address with. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).
- `POST /api/auth/password` — SW-ADR-148 D: self-service password change, current password required. Signs out every OTHER session and not this one. Returns an unnamed dict {signed_out_elsewhere: int}, so response_model is omitted the way the 204 routes omit it - there is no convention here for a named-but-anonymous body. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).
- `POST /api/auth/deactivate` — SW-ADR-148 A. 204. Reversible - 'pause me', distinct from DELETE /api/auth/me. CONFLICT (field is_active) when the caller is the last active administrator. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).
- `DELETE /api/auth/me` — CR-001 / SW-ADR-150. 204. Deletion is SOFT: sets deleted_at and is_active=false and revokes every session in one transaction. Every expense, category, audit row and the person record survive. spendwise_app holds no DELETE grant on users, so hard deletion is impossible for the runtime role rather than merely unimplemented. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).
- `GET /api/auth/export` — SW-ADR-148 B. Returns an unnamed dict of the caller's own rows, so response_model is omitted - see POST /api/auth/password. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).
- `GET /api/admin/overview` — Counts and dates only, never an amount or a description (CONSTITUTION Art VI.1). Audited read: writes one admin_audit_log row per request in the same transaction (SW-ADR-135). NO SINGLE ADR AUTHORISES THIS ROUTE - it arrived with M4 in commit 8e75a4c and no record names it; CR-001_CONTRACT.md 5.2 only amended its deactivated/deleted split. Recorded as not-determinable rather than attributed to a record that does not say it. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).
- `GET /api/admin/users/{user_id}/spending` — CR-001 / SW-ADR-151. The ONE admin route that carries money. A total and a daily series, and deliberately NO category_id parameter and no by_category in the response - the same sentence that granted this withheld the categories. Same range rules as GET /api/expenses/summary through the same require_range helper. no P-xxx id exists for this route. It was approved by ADR after the PRD's spec ids were assigned, and no Bible story cites it either. Recorded as a gap rather than filled with an invented id (CLAUDE.md status law).

<!-- END GENERATED ROUTES -->

**Status codes.** 200 read · 201 create · 204 delete · 400 malformed · 401 unauthenticated ·
403 authenticated but forbidden by role · **404 not-yours-or-not-found on every verb**
(`P-PRV-03`) · 409 conflict (duplicate email, duplicate category name, last-administrator guard)
· 422 validation · 429 rate limited, with `Retry-After`.

<!-- BEGIN GENERATED §6.1 — py "docs/03 PRD/api/generate_api.py" -->

### §6.1 — Two worked payloads

**Generated from `docs/03 PRD/api/contract.json`. Do not hand-edit — regenerate.**

The first version of this section was hand-written to answer a cold reader who had asked
eight variants of one question: *what does the JSON actually look like?* The next cold
reader found that the hand-written answer omitted `by_day` (which `SRC-001 §7.4` requires
and five other documents assert on), said `daily_average_paise: 0` where six documents say
`null`, named two categories that do not exist, printed `by_category` out of the order the
same page mandates, dropped `color` and `percent`, and cited the wrong ADR for the one
number that is never waivable.

**A hand-written example is exactly as driftable as the prose it replaces** — and once it
is labelled normative it drifts with authority. So it is computed now, from the same spec
that states the rules. These payloads are **normative**: where prose and payload disagree,
that is a defect to be filed, not a choice.

**Creating an expense.** `POST /api/expenses`, cookie-authenticated as user 7.

```json
{
  "amount": "1250.00",
  "category_id": 3,
  "description": "Auto to office",
  "spent_on": "2026-08-01",
  "user_id": 99,
  "id": 4242
}
```

`amount` is a **decimal string**, in rupees, and is the only accepted form — a JSON number
is rejected 422, because a float cannot hold ₹0.10 exactly `[SRC: SW-ADR-029]`. More than
two decimal places is rejected, never rounded `[SRC: SW-ADR-112]`. `user_id` and `id` are
**silently discarded before validation**: the owner is the verified identity, never the
body `[SRC: SW-ADR-130]`. Response **201**:

```json
{
  "id": 8801,
  "user_id": 7,
  "category_id": 3,
  "category_name": "Transport",
  "amount": "1250.00",
  "amount_paise": 125000,
  "currency": "INR",
  "description": "Auto to office",
  "spent_on": "2026-08-01",
  "receipt_key": null,
  "created_at": "2026-08-01T09:14:22.481Z",
  "updated_at": null
}
```

`user_id` is **7**, not the forged 99, and `id` is server-assigned. Both `amount` (display,
rupees) and `amount_paise` (the stored integer) are returned: the client never divides by
100, and a test can assert on the exact integer. `created_at` is UTC with an offset; the
*calendar* boundary is Asia/Kolkata `[SRC: SW-ADR-096]`.

**The day-one summary.** `GET /api/expenses/summary?from=2026-08-01&to=2026-08-31`

Against the seeded fixture, as person A, today mocked to `2026-08-05` Asia/Kolkata. **This is
the payload the never-waivable gate asserts on**, and every value below is computed
from `contract.json` — none is typed.

```json
{
  "from": "2026-08-01",
  "to": "2026-08-31",
  "total_paise": 379049,
  "total": "3790.49",
  "count": 4,
  "days_elapsed": 5,
  "daily_average_paise": 75810,
  "daily_average": "758.10",
  "by_category": [
    {
      "category_id": 1,
      "category_name": "Groceries",
      "color": "#4a7c59",
      "total_paise": 210000,
      "count": 1,
      "percent": 55
    },
    {
      "category_id": 3,
      "category_name": "Transport",
      "color": "#3e6b8f",
      "total_paise": 125000,
      "count": 1,
      "percent": 33
    },
    {
      "category_id": 5,
      "category_name": "Health",
      "color": "#2e7d8a",
      "total_paise": 34050,
      "count": 1,
      "percent": 9
    },
    {
      "category_id": null,
      "category_name": "Uncategorised",
      "color": "#928a85",
      "total_paise": 9999,
      "count": 1,
      "percent": 3
    }
  ],
  "by_day": [
    {"date": "2026-08-01", "total_paise": 125000, "count": 1},
    {"date": "2026-08-02", "total_paise": 0, "count": 0},
    {"date": "2026-08-03", "total_paise": 244050, "count": 2},
    {"date": "2026-08-04", "total_paise": 0, "count": 0},
    {"date": "2026-08-05", "total_paise": 9999, "count": 1},
    {"date": "2026-08-06", "total_paise": 0, "count": 0},
    … 2026-08-07 … 2026-08-31, all total_paise 0, count 0 — 31 rows in total
  ]
}
```

Every field, spelled out, because each was guessed at least once by a cold reader:

- `total_paise` **379049** = 125000 + 34050 + 210000 + 9999. Integers throughout `[SRC: SW-ADR-029]`.
- `count` **4** — the number of expense **rows**, not the number of days.
- `days_elapsed` **5** — `max(0, min(to, today) − from + 1)`, inclusive of both ends
  `[SRC: SW-ADR-085]`, capped at today, evaluated in Asia/Kolkata `[SRC: SW-ADR-053]`.
  **This is the divisor, and it is days, not rows.**
- `daily_average_paise` **75810** — `379049 / 5`, rounded **half-up** `[SRC: SW-ADR-010]`,
  in integers: `(2·total + elapsed) // (2·elapsed)`. Two wrong answers to avoid —
  **75809** is what truncation gives, and **94762** is what dividing by `count` gives.
- `daily_average` **"758.10"** — the same value as a display string, trailing zero kept.
- **`daily_average_paise` is `null`, never `0`, when `days_elapsed` is 0**
  `[SRC: SW-ADR-053, SW-ADR-054]` — a future-dated range has no average, and `0` would
  read as "spent nothing". `P-UND-02` renders it `—`; that dash is the client's.
- `by_category` is ordered `total_paise` **descending**, then name ascending
  `[SRC: SW-ADR-055]`, with the synthetic `null` bucket **always last regardless of size**
  `[SRC: SW-ADR-131]`, labelled `Uncategorised` and rendered `#928a85`. It is a bucket, not a
  row in `categories`; nothing joins to it. `percent` is largest-remainder, so the printed
  percentages sum to exactly 100.
- `by_day` carries **one row per calendar day, including days with no spending**
  `[SRC: SRC-001 §7.4]` — 31 rows here. Build it with `generate_series` and a LEFT JOIN,
  with the owner predicate in the **`ON`** clause: move it to `WHERE` and the LEFT JOIN
  degenerates to an INNER JOIN, the zero days vanish, and only `SIT-E0-S9-05` notices.
- An empty range returns `total_paise: 0`, `count: 0`, `by_category: []`, and a `by_day`
  still full of zero rows — **zeros and empty arrays, not `null`**. That is not a
  contradiction of the null policy in §6.3 (An absent value is `null`, never omitted, never an empty string):
  a field that HAS no value is `null`; a total that IS zero is `0`.

**Error codes** are enumerated in `docs/03 PRD/api/error_codes.md`, generated from the same
spec. The list is closed: a code not on it cannot be returned.

### §6.2 — Conventions a cold reader had to invent

**Generated from `contract.json`. Do not hand-edit — regenerate.**

Every row below is something an engineer with only these documents had to **guess**.
A guess is a document defect, so each is ruled here rather than left to be
re-invented differently by the next reader. The last column records which uncoached
slice raised it — this table is a record of where the document set was thin, not
only of what it now says.

| | Question | Ruling | Why | Source | Raised by |
|---|---|---|---|---|---|
| `CV-01` | What is the session cookie called? | **`sw_session`. httpOnly, SameSite=Lax, Path=/, Secure driven by COOKIE_SECURE.** | SIT-E0-S5-02 asserts on a cookie the test must be able to find by name, and the name was never written down. Every attribute was specified exhaustively; the name was not. | P-ACC-03 · SW-ADR-014 | slice run 2, guess 3 |
| `CV-02` | How is the uncategorised-only filter expressed? | **`?uncategorised=true`. It is mutually exclusive with `category_id`; sending both is 422.** | P-UND-05 makes the synthetic bucket clickable, so it needs a query parameter, and `category_id=null` is not expressible in a query string. | P-UND-05 · SW-ADR-109 | slice run 2, guess 9 |
| `CV-03` | Does the day series re-scope under a category filter? | **Yes. The filter re-scopes the total, the count, the average, the day series and the entry list. ONLY `by_category` is left un-scoped.** | P-UND-01 says 're-scopes everything except the breakdown itself'; the breakdown is what you would be clicking, so re-scoping it would collapse the control. | P-UND-01 · SW-ADR-109 | slice run 2, guess 10 |
| `CV-04` | Does "1250.0000" pass? Written scale, or numeric value? | **Rejected, 422. The rule is on the WRITTEN scale: more than two decimal places as typed is refused, even when the extra places are zeros.** | SW-ADR-112 refuses rather than rounds, and stricter wins (Art II.1). A value-based rule would silently accept input the person may have mistyped. | SW-ADR-112 · NEG-M-04 | slice run 2, guess 11 |
| `CV-05` | Where does `currency` come from on insert? | **`get_current_user` returns a principal carrying `currency`; the expenses service reads it from the principal, never from the users table.** | SW-ADR-013 snapshots it at write time, and SRC-001 §3.4 forbids the expenses module touching `users`. The principal is the sanctioned carrier. | SW-ADR-013 · SRC-001 §3.4 | slice run 2, guess 12 |
| `CV-06` | How is "today" mocked for the gate? | **`app/core/clock.py` exposes `today_ist()` behind a FastAPI dependency, overridden in tests. NOT a library that freezes the process clock.** | Freezing the process clock does not freeze `now()` inside Postgres, so session expiry and `spent_on` validation would disagree about what day it is. | SW-ADR-096 · Bible E0-S9 | slice run 2, guess 14 |
| `CV-07` | Are `from` and `to` required on the summary? | **Both required. Omitting either is 422; there is no default range.** | P-UND-03: 'the server never guesses this month'. A default would be the server guessing. | P-UND-03 · SW-ADR-108 | slice run 2, guess 15 |
| `CV-08` | Does the create response carry `category_name`? | **Yes. The sanctioned service-to-service crossing of SW-ADR-017 covers BOTH the summary and the create/update responses - two paths, not one.** | The client renders the new row immediately; without the name it would need a second request, which is the round trip SRC-001 asked to avoid. | SW-ADR-017 · P-REC-01 | slice run 2, guess 16 |
| `CV-09` | What sets `updated_at`? | **The service, on PATCH only. No database trigger. A create leaves it null.** | A trigger would fire on the audit-log-adjacent writes too and make 'never edited' unrepresentable. Null means never edited, and that is a fact worth keeping. | P-REC-03 · datamodel.json | slice run 2, guess 18 |
| `CV-10` | Does a 201 carry a `Location` header? | **No. The created resource is in the body; there is no separate fetch to point at.** | One convention, stated once, rather than a per-endpoint judgement call. | SW-ADR-051 | slice run 2, guess 19 |
| `CV-11` | Route ordering, and what a non-integer id returns | **`/api/expenses/summary` MUST be declared before `/api/expenses/{expense_id}`. A path parameter that fails integer coercion returns **404**, not 422.** | Declared the other way, the literal `summary` is eaten by the int path parameter and the endpoint 422s. And a malformed id is a not-found id: 422 would leak that the id space is integers, which P-PRV-03's uniform 404 exists to avoid. | P-PRV-03 · SW-ADR-050 | slice run 2, guess 20 |
| `CV-12` | Who commits the request transaction? | **The session dependency commits ONCE, after the handler returns. No service and no repository commits.** | The GUC is transaction-local, and the create response stitches `category_name` from the categories service AFTER the insert. Commit in the service and that read returns zero rows - `category_name` silently becomes null with nothing red. | SW-ADR-136 D · GOTCHAS | slice run 3, guess 1 |
| `CV-13` | How does an expected constraint violation not abort the request? | **The INSERT runs inside a SAVEPOINT. On the composite-FK violation, ROLLBACK TO SAVEPOINT, then return 422 field=category_id.** | One transaction per request plus 'enforced by the database' means the FK violation aborts the REQUEST transaction. Without a savepoint the handler cannot emit its 422 and returns 500 - and the naive fix, a second transaction, is the silent zero-rows failure SW-ADR-136 D forbids. | SW-ADR-072 · P-REC-01 · NEG-X-11 | slice run 3, guess 10 |
| `CV-14` | How is 'today' pinned for the BROWSER-observed gate run? | **The clock dependency reads `APP_TODAY_OVERRIDE` when set. Absent in production; set in the gate container. The FastAPI dependency override of CV-06 covers in-process tests only.** | Art IX.4 and E0-S10 require the gate observed through a real browser against a running app, where no in-process override is reachable - so CV-06 alone could not produce the observed 75810. | SW-ADR-096 · Art IX.4 · CV-06 | slice run 3, guess 4 |
| `CV-15` | Does the breakdown-sums-to-total invariant hold under a filter? | **It is asserted ONLY when no category filter is applied. With a filter the headline re-scopes and `by_category` does not, so they are not expected to agree.** | P-UND-05 states the invariant unqualified and CV-03 leaves by_category un-scoped. Both are right; the invariant simply has a precondition nobody wrote down, and a literal test walks straight into it. | P-UND-05 · CV-03 · SW-ADR-109 | slice run 3, contradiction C3 |
| `CV-16` | What is the test stack? | **pytest + pytest-asyncio + httpx (ASGITransport) for API and unit tests; Playwright for the browser-observed gate. Added to SW-ADR-016's locked stack.** | Art IX.1 mandates failing-test-first and E0-S5 mandates a real browser, while SW-ADR-016 says do not substitute and named no tool for either - so the first engineer had to extend a stack the same document forbids extending. | SW-ADR-016 · Art IX.1 · E0-S5 | slice run 3, guess 13 |
| `CV-17` | How is the percentage tie-break resolved? | **Integer arithmetic only. Ties go to the EARLIER position in the already-sorted list (total DESC, name ASC, synthetic last). Never float division.** | Art V.1 says never a float, and the generator that produces the normative payload used float division - so the only statement of the algorithm violated the Constitution, and its tie-break was an accident of Python's sort stability. | SW-ADR-055 · Art V.1 | slice run 3, contradiction C8 |
| `CV-18` | What does a foreign category_id filter return on the summary? | **The filter APPLIES and matches nothing: total_paise 0, count 0, by_day all zeros, daily_average_paise computed over the elapsed days (so 0, not null). `by_category` stays un-scoped per CV-03 and is non-empty.** | NEG-X-08 said both 'B's OWN summary' and 'an unknown category_id filters to nothing' in one cell - the first reads as ignore the filter, the second as total 0. | NEG-X-08 · CV-03 · P-PRV-03 | slice run 3, guess 12 |
| `CV-19` | May an optional field be sent as explicit null? | **Yes. Explicit `null` and omission are equivalent on input. Unknown keys are discarded, never rejected.** | `extra="forbid"` would 422 the forged `user_id` of NEG-X-10, which must return 201. | SW-ADR-130 · SW-ADR-141 | slice run 4, guess 6 |
| `CV-20` | What format does APP_TODAY_OVERRIDE take? | **`APP_TODAY_OVERRIDE=2026-08-05` — a bare ISO date, parsed with `date.fromisoformat`, read as an Asia/Kolkata calendar date. Malformed: refuse to start (P-OPS-01 fails fast).** | CV-14 exists because the in-process override of CV-06 cannot reach a browser-observed run, and it stopped one line short of being executable. | CV-14 · SW-ADR-096 | slice run 4, guess 8 |
| `CV-21` | Which rule owns a non-string `amount` that is not a number either? | **`amount.grammar` owns EVERY non-conforming amount - boolean, array, object, number. `amount` is modelled as `Any` and grammar-checked; it never reaches `field.type`.** | One concept, one sentence. The `amount` row of the field.type placeholder table is therefore unreachable and is removed. | NEG-M-06 · SW-ADR-142 | slice run 5, guess 6 |
| `CV-22` | Is `description` trimmed, and is 500 measured before or after? | **Whitespace-only becomes `null` FIRST; the length is then measured on the survivor. A non-empty description is stored **verbatim** - never trimmed.** | SW-ADR-115 says normalised to null, not stripped. Trimming would silently alter what the person typed, which SW-ADR-112 refuses to do for amounts. | SW-ADR-115 · SW-ADR-112 | slice run 5, guess 7 |
| `CV-23` | How is `today ± N years` computed at the boundary? | **Calendar arithmetic (`relativedelta`), clamping 29 February to 28 February. Never fixed day counts.** | Every other date rule here is calendar-based and Asia/Kolkata-anchored; the two readings differ by up to three days, exactly on the boundary NEG-M-08/09 probe. | SW-ADR-111 · SW-ADR-096 | slice run 5, guess 8 |
| `CV-24` | How is database state reset between test cases? | **Function-scoped reset on a **separate `spendwise_owner` connection owned by the test fixture** - not the app, not the seeder:

    TRUNCATE users, sessions, categories, expenses, password_resets,
             admin_audit_log RESTART IDENTITY CASCADE;

then reseed through the real endpoints. NOT the outer-transaction-and-rollback pattern.** | That pattern is unavailable here and nothing said so. It contradicts CV-12 (the dependency commits, once, per request) and it breaks `set_config(..., true)`, which is transaction-local - nest the request inside an outer transaction and the GUC's lifetime stops matching the request's. The seed README states isolation 'between runs'; between CASES was never stated, and it bites immediately: a test that creates a fifth expense makes the day-one gate read 379049 + n and fail for a reason that has nothing to do with the code. Two further things were unstated and each breaks immediately. **Role:** `spendwise_app` holds no DELETE on `users` and `verify_invariants.sql` check 11 asserts it cannot - so the runtime role cannot perform the truncate. **RESTART IDENTITY:** plain TRUNCATE does not reset a GENERATED ALWAYS AS IDENTITY sequence, so the second test case's A gets categories 17-24 and every by_category assertion in expected_summary.json fails. That phrase appeared NOWHERE in the document set. The fixture owns the connection so seed/README.md's rule - 'the seeder does not acquire a user-deletion path by the back door' - still holds of the seeder. | seed/README.md · CV-12 · SW-ADR-136 D | slice run 6, guess 6 |
| `CV-25` | Truncate or round when rendering a timestamp to 3 fractional digits? | ****Truncate, never round.**** | `now()` yields microseconds and rounding can carry into the next second, moving a timestamp across a boundary - including a day boundary, which is the one thing the Asia/Kolkata rule exists to get right. | serialisation.datetime | slice run 6, guess 7 |
| `CV-26` | What caching posture do authenticated JSON responses take? | ****`Cache-Control: no-store` on every `/api/*` response.**** | The deployment has no TLS (SW-ADR-014, a recorded weakness), and FastAPI's default is no header at all, which permits heuristic caching of a summary. A money response cached by an intermediary is a cross-person leak achieved without touching the database. | SW-ADR-014 · P-OPS-05 | slice run 6, guess 8 |

A convention absent from this table and from §6.1 is **not** a licence to choose one.
It is an `OPEN` item: escalate, never invent (`CONSTITUTION.md` Art X).

### §6.3 — Serialisation

| | |
|---|---|
| **Timestamps** | UTC, RFC 3339 with a `Z` suffix and exactly 3 fractional digits: `2026-08-01T09:14:22.481Z`. Not the framework default - configure the encoder. |
| **Dates** | ISO 8601 date only, no time component: `2026-08-01`. |
| **Money** | `amount` and `total` and `daily_average` are decimal STRINGS in rupees with exactly two places. `*_paise` fields are integers. The client never divides by 100. |
| **Nulls** | An absent value is `null`, never omitted, never an empty string. |
| **Unknown body keys** | `extra="ignore"` model-wide. An unknown key is discarded, never 422 - `extra="forbid"` would reject the forged `user_id` of NEG-X-10, which must return 201 (SW-ADR-130). |
| **`amount` grammar** | `^-?[0-9]{1,15}(\.[0-9]+)?$` — applied **before** `Decimal()`. Applied BEFORE Decimal(). It checks SHAPE, not scale: decimal places are counted by `amount.scale`, which owns the sentence P-REC-01 quotes. An earlier pattern capped the fraction at two digits AND was ordered before amount.scale, which made amount.scale unreachable dead text - so `12.345` returned 'Amount must be a decimal string' instead of 'Amount must have at most two decimal places.', the sentence P-REC-01 states. Found by the fifth uncoached slice, contradiction C1. Rejects scientific notation, surrounding whitespace, a leading '+', and a bare '.50'. |

Rejected by that pattern: `1.25e3`, ` 12.50 `, `+12.50`, `.50`, `abc`, `1,250.00`.

Rejected by `amount.scale`, **not** by the pattern: `1250.0000`, `12.345` — the grammar checks shape,
the scale rule counts decimal places and owns `P-REC-01`'s sentence.

**Transaction.**

| | |
|---|---|
| **Isolation** | **REPEATABLE READ** on any request that reads the summary. The level is selected **on the connection at checkout, before `BEGIN`** — in SQLAlchemy, `engine.connect().execution_options(isolation_level='REPEATABLE READ')` behind a second session dependency (`get_db_rr`) that only the summary route declares. |
| **Level selection** | The level is resolved from a module-level route table, `REPEATABLE_READ_ROUTES = {('GET', '/api/expenses/summary')}`, consulted by the factory — so it cannot depend on dependency-resolution order. `get_db_rr` stays declared on the route as documentation, and a **boot assertion fails closed** if the declared markers and the table disagree. |
| **Session ownership** | **One session factory, one AsyncSession, one transaction — held on `request.state.db`.** `get_db` and `get_db_rr` both delegate to it; a second call asking for a DIFFERENT isolation level raises rather than silently reusing the wrong one. |
| **Commit** | The session dependency commits ONCE, after the handler returns (CV-12). |
| **Write path** | READ COMMITTED is correct for the create path: it takes one snapshot per statement and there is only one statement inside the savepoint. |
| **A write inside the snapshot** | The summary transaction is REPEATABLE READ and contains a WRITE - the `last_seen_at` heartbeat. Two concurrent requests on one session that both see it stale will both UPDATE the row, and under REPEATABLE READ the loser gets **40001, could not serialize access due to concurrent update**, and the request dies. Under READ COMMITTED it would simply block and succeed. J-U-09 documents the dashboard firing several requests at once, so this is a 500 on the dashboard, intermittently, in production only. **The bump runs inside its own SAVEPOINT; on 40001 the savepoint is rolled back and the request continues** - losing one bump is harmless, because the transaction that won already performed it. |

### §6.4 — Request models

**Generated from `contract.json`. Do not hand-edit — regenerate.**

`models` held only the RESPONSE shapes. `ExpenseCreate` and `Principal` appeared as bare strings in the route table and were defined nowhere - so the half of the contract every 422 test touches was outside the spec of record that SW-ADR-138 created precisely because hand-written shapes drift.

**Null policy.** An optional field may be sent as explicit `null` or omitted; the two are equivalent. Unknown keys are discarded, never rejected (`extra="ignore"`, CV-19 / SW-ADR-130).

**`ExpenseCreate`** — P-REC-01 · SW-ADR-130

| Field | Type | Required | |
|---|---|---|---|
| `amount` | `string` | **yes** | decimal string in rupees; a JSON number is 422 (amount.grammar) |
| `spent_on` | `date` | **yes** | never defaulted server-side (SW-ADR-111) |
| `category_id` | `integer|null` | no | ownership enforced by the composite FK, not a pre-read (SW-ADR-072) |
| `description` | `string|null` | no | empty or whitespace-only is normalised to null (SW-ADR-115) |

Discarded before validation: `user_id`, `id`, `amount_paise`, `currency`, `created_at`, `updated_at`, `receipt_key`, `category_name`. Discarded BEFORE validation, never 422 (SW-ADR-130). NEG-X-10 requires 201 for a forged user_id, so extra="forbid" is not available.

**`ExpenseUpdate`** — P-REC-03

Every field optional; at least one must be present or 422 field.required with field='body'. The service sets updated_at (CV-09).

| Field | Type | Required | |
|---|---|---|---|
| `amount` | `string` | no |  |
| `spent_on` | `date` | no |  |
| `category_id` | `integer|null` | no |  |
| `description` | `string|null` | no |  |

**`Principal`** — P-ACC-06

A response model, but listed here because the route table names it and `models` did not define it.

| Field | Type | Required | |
|---|---|---|---|
| `id` | `integer` | — |  |
| `email` | `string` | — |  |
| `display_name` | `string` | — |  |
| `role` | `string` | — | `user` or `admin` |
| `currency` | `string` | — | the expenses service reads currency from HERE, never from the users table (CV-05, SRC-001 §3.4) |
| `is_active` | `boolean` | — |  |
| `receipts_enabled` | `boolean` | — | Required by P-ACC-06 so the client can hide the receipt control when storage is unconfigured rather than letting it fail. It was MISSING from this model, which SW-ADR-141 added to the spec of record in order to stop drift - and which drifted in the same commit. Bible E1-S8 AC2, SIT-E1-S8-02, SIT-E5-S3-01, P-RCP-03 and 08_failure_modes.md all assert it. Found by the fifth uncoached slice, C3. |

**`RegisterRequest`** — P-ACC-01

| Field | Type | Required | |
|---|---|---|---|
| `email` | `string` | **yes** |  |
| `password` | `string` | **yes** | 12-72 bytes (SW-ADR-103) |
| `display_name` | `string` | **yes** |  |

**`LoginRequest`** — P-ACC-03

| Field | Type | Required | |
|---|---|---|---|
| `email` | `string` | **yes** |  |
| `password` | `string` | **yes** |  |

**`ResetCompleteRequest`** — P-ACC-07

| Field | Type | Required | |
|---|---|---|---|
| `token` | `string` | **yes** | the raw code; the row stores its SHA-256 |
| `password` | `string` | **yes** |  |

**`CategoryCreate`** — P-REC-05

| Field | Type | Required | |
|---|---|---|---|
| `name` | `string` | **yes** | 1-50 chars, unique per person case-insensitively |
| `color` | `string` | **yes** | ^#[0-9a-f]{6}$ |

**`CategoryUpdate`** — SW-ADR-114

At least one must be present or 422 field.required with field='body'.

| Field | Type | Required | |
|---|---|---|---|
| `name` | `string` | no |  |
| `color` | `string` | no |  |

**`UploadUrlRequest`** — P-RCP-01

The object key is NEVER accepted from the client (P-RCP-02); it is server-derived.

| Field | Type | Required | |
|---|---|---|---|
| `content_type` | `string` | **yes** | allowlist: jpeg, png, webp, pdf |
| `content_length` | `integer` | **yes** | <= 10 MB |

**`AttachRequest`** — P-RCP-01

| Field | Type | Required | |
|---|---|---|---|
| `expense_id` | `integer` | **yes** |  |
| `staging_key` | `string` | **yes** | must be under staging/{caller_id}/ |

**`ActiveRequest`** — P-ADM-05

| Field | Type | Required | |
|---|---|---|---|
| `is_active` | `boolean` | **yes** |  |

**`RoleRequest`** — P-ADM-06

| Field | Type | Required | |
|---|---|---|---|
| `role` | `string` | **yes** | `user` or `admin`; last-admin guard is 409 |

**`SummaryQuery`** — P-UND-01…P-UND-06 · CV-02 · CV-07 · SW-ADR-144

Five of the thirteen validation rules - range.required, range.order, range.span, range.floor, filter.exclusive - fire ONLY here, and `precedence.tie_break` resolves same-class collisions by 'the order the request model declares them'. There was no such model, so `?from=x&to=y` (both failing field.type) had no stated expected `field`.

| Field | Type | Required | |
|---|---|---|---|
| `from` | `date` | **yes** | no default range; the server never guesses |
| `to` | `date` | **yes** |  |
| `category_id` | `integer|null` | no |  |
| `uncategorised` | `boolean` | no | strict: only true/false. `false` is treated as absent. Mutually exclusive with category_id (CV-02) |

**`ExpenseListQuery`** — P-REC-02 · SW-ADR-038

| Field | Type | Required | |
|---|---|---|---|
| `from` | `date` | no |  |
| `to` | `date` | no |  |
| `category_id` | `integer|null` | no |  |
| `limit` | `integer` | no | maximum 200 |
| `offset` | `integer` | no | NEG-X-12 requires '422 naming offset' for offset=-1; the rule is `offset.bounds` |

**`ProfileUpdate`** — SW-ADR-148 C

| Field | Type | Required | |
|---|---|---|---|
| `display_name` | `string|null` | no | the only field. Email is absent deliberately (SW-ADR-012) |

**`PasswordChange`** — SW-ADR-148 D

| Field | Type | Required | |
|---|---|---|---|
| `current_password` | `string` | **yes** |  |
| `new_password` | `string` | **yes** | 12-72 bytes; bcrypt IGNORES bytes past 72 (SW-ADR-103) |

<!-- END GENERATED §6.1 -->

---

## §7 — Cross-cutting floors

| | |
|---|---|
| **Isolation** | `P-PRV-01`. Two layers, every command, `WITH CHECK`. Red-proofed. |
| **Money** | Integer paise. Exact decimal at the boundary only. `SUM()` cast back to a bounded integer — the numeric sum cannot overflow, but the cast can, which the `≤ 10¹²` constraint keeps safe `[SRC: SW-ADR-079]`. |
| **Time** | Asia/Kolkata for every calendar boundary. All timestamps stored with a timezone, in UTC. `spent_on` is a plain date the person chose. |
| **Modules** | A module touches only its own tables. The one sanctioned crossing is the summary's category names, service-to-service `[SRC: SW-ADR-017]`. Per-table ownership and policy map in `P-PRV-02` above, as `SW-ADR-043` directed and `SW-ADR-129` settled. |
| **Rate limits** | `SW-ADR-128`. **Global: 120/min per authenticated user id, 60/min per IP on unauthenticated API paths** (configured 60 and 30); static assets unlimited. Per-route floors are stated on `P-ACC-01` (register 5/min per IP **and 20/day per IP**), `P-ACC-03` (login 10/min per IP and 10/min per email) and `P-ACC-07` (reset 6/min per IP). Effective figures; configured at half because the store is per-process across two workers. Client IP from the socket unless a trusted proxy is declared `[SRC: SW-ADR-048]`. |
| **Errors** | One envelope. One convention. Every code is testable. |

---

## §8 — Colophon

Every `P-` row cites a source and a BRD row. Coverage against the BRD — both directions, no-gap
and no-creep — is computed and reported in this goal's evidence rather than asserted here.

**No `P-` row is `OPEN`.** That is not because nothing was unsettled — 38 rows were — but because
they were escalated to Fable 5 and ruled on 2026-08-05 under the client's explicit instruction.
Four of those rulings are flagged for the client's digest and any of them can be reversed with
one message; this document would then be re-derived, not patched.

---

## §9 — Coverage map: every BRD row to the specification that satisfies it

**No-gap made checkable rather than claimed.** Every requirement in `02 BRD` appears below.
A row with no entry would be a hole; a `P-` row citing no requirement would be scope creep.
Both directions are recomputed on every change — see this goal's evidence.

| BRD requirement | Satisfied by |
|---|---|
| `R-ACC-01` | P-ACC-01 |
| `R-ACC-02` | P-ACC-03 |
| `R-ACC-03` | P-ACC-05 |
| `R-ACC-04` | P-ACC-04, P-ACC-06 |
| `R-ACC-05` | P-ACC-07, P-ADM-04 |
| `R-ACC-06` | P-ACC-02 |
| `R-ACC-07` | P-ACC-04 |
| `R-ACC-08` | P-ACC-03 |
| `R-ACC-09` | P-ACC-01 |
| `R-ACC-10` | P-ACC-01 |
| `R-REC-01` | P-REC-01, P-REC-02 |
| `R-REC-02` | P-REC-01, §7 Money |
| `R-REC-03` | P-REC-03, P-REC-04 |
| `R-REC-04` | P-REC-05 |
| `R-REC-05` | P-REC-05 |
| `R-REC-06` | P-REC-05 |
| `R-REC-07` | P-RCP-01 |
| `R-REC-08` | P-REC-01 |
| `R-REC-09` | P-REC-01 |
| `R-REC-10` | P-REC-01 |
| `R-REC-11` | P-REC-04, P-REC-05, §5.3 |
| `R-UND-01` | P-UND-01 |
| `R-UND-02` | P-UND-03 |
| `R-UND-03` | P-UND-01 |
| `R-UND-04` | P-UND-02 |
| `R-UND-05` | P-UND-05, §5.2 |
| `R-UND-06` | P-UND-01 |
| `R-UND-07` | §5.2 |
| `R-UND-08` | P-UND-02, P-UND-03 |
| `R-UND-09` | P-UND-05 |
| `R-UND-10` | P-UND-06 |
| `R-UND-11` | P-UND-07 |
| `R-UND-12` | P-UND-04 |
| `R-RCP-01` | P-RCP-01, P-RCP-02 |
| `R-RCP-02` | P-RCP-02 |
| `R-RCP-03` | P-RCP-03 |
| `R-RCP-04` | P-RCP-01 |
| `R-RCP-05` | P-RCP-01, P-REC-04 |
| `R-ADM-01` | P-ADM-01 |
| `R-ADM-02` | P-ADM-02 |
| `R-ADM-03` | P-ADM-03 |
| `R-ADM-04` | P-ADM-04 |
| `R-ADM-05` | P-ADM-05 |
| `R-ADM-06` | P-ADM-06 |
| `R-ADM-07` | P-ADM-07 |
| `R-ADM-08` | P-ADM-08 |
| `R-ADM-09` | P-ACC-07 |
| `R-ADM-10` | P-ADM-04 |
| `R-ADM-11` | P-ADM-06 |
| `R-ADM-12` | P-ADM-09 |
| `R-PRV-01` | P-PRV-01, P-PRV-03 |
| `R-PRV-02` | P-PRV-02 |
| `R-PRV-03` | P-PRV-04 |
| `R-PRV-04` | P-PRV-04 |
| `R-PRV-05` | P-PRV-04 |
| `R-PRV-06` | P-ADM-02 |
| `R-PRV-07` | P-PRV-05 |
| `R-PRV-08` | P-PRV-06 |
| `R-OPS-01` | P-OPS-02 |
| `R-OPS-02` | P-OPS-01, P-OPS-04 |
| `R-OPS-03` | §2 (scope, carried from BRD) |
| `R-OPS-04` | §7 Modules |
| `R-OPS-05` | P-OPS-02 |
| `R-OPS-06` | P-OPS-03, P-OPS-05 |
| `N-ISO-01` | P-PRV-01 |
| `N-ISO-02` | P-PRV-01, §7 Isolation |
| `N-ISO-03` | P-PRV-01 |
| `N-MON-01` | P-REC-01, §7 Money |
| `N-SEC-01` | P-ACC-03 |
| `N-SEC-02` | P-ACC-05, P-ADM-03 |
| `N-SEC-03` | P-ACC-03 (cookie), §2 |
| `N-SEC-04` | P-ACC-01, P-ACC-03, P-ACC-07, §7 Rate limits |
| `N-AVL-01` | P-OPS-02 |
| `N-OPS-01` | P-OPS-01 |
| `N-UX-01` | §5.2 (phone width) |
| `N-UX-02` | §5, design system |
| `N-A11Y-01` | §5.2, design system §6 |

**76 BRD rows, all covered.** Where the satisfying entry is a section rather than a
`P-` row, that is deliberate: cross-cutting rules (money, isolation, modules, phone width) are
stated once in §5 or §7 rather than repeated into every specification that depends on them.
