# Journey — the Administrator

| Field | Value |
|---|---|
| Persona | **Administrator** (`admin`) — keeps accounts working. Also a person, with their own spending. |
| Derived from | `02 BRD` §3 · `03 PRD` §4 E5–E6, §5.3 |
| Purpose | Find the seams. **Every step cites the `P-` row that specifies it.** |

> The administrator exists for **one stated reason**: *"I need someone to be able to reset a
> password when a user locks themselves out"* — `SRC-001 §1`.

---

## J-A-01 — Becoming the administrator

Fresh database, `BOOTSTRAP_ADMIN_EMAIL` set. The first account created **by that address** claims
administrator. `P-ACC-02`

If the variable is unset and no administrator exists, **the application refuses to start** — a
loud five-second failure instead of a silent, permanent lockout in which nobody can ever promote
anyone. `P-ACC-02`, `SW-ADR-049`

**Seam checked:** as `SRC-001 §4.4` was written, whoever found a fresh deployment first became
administrator. Closed. ✅

## J-A-02 — Someone cannot get in

| # | Intent | What happens | Spec |
|---|---|---|---|
| 1 | Finds the account. | Search by email or display name. Sees email, name, role, active, created, last-active. **No spending figure anywhere.** | `P-ADM-01` |
| 2 | Wonders what they spent. | **Cannot.** Not hidden in the interface — the response model has no field capable of holding an amount, and the database policy admits only aggregate reads. | `P-PRV-02` |
| 3 | Issues a reset. | Confirms: *"Issue a password reset for {email}? All their sessions will end."* | `P-ADM-04`, §5.3 |
| 4 | Reads the code. | Shown **once**, never logged — the deny-list is red-proofed by planting the value and asserting its absence. | `P-ADM-04`, `P-OPS-05` |
| 5 | Hands it over. | Out of band. There is no email in the stack. | `P-ADM-04` |
| 6 | Checks the record. | One `password_reset_issued` row, written in the same transaction. Its detail shape **structurally cannot** carry the code. | `P-PRV-04` |

**Seam checked:** step 4. Had the audit detail been free-form JSON, a helpful "reset issued" row
carrying the token would have written a live credential into a permanent, admin-readable table —
undoing the hashing rule entirely. Closed by the nine-type allowlist. ✅

## J-A-03 — Ending a session

Force sign-out. Confirms, naming the count. Revoked immediately; the person's next request 401s
and their client shows a reason banner rather than failing silently. `P-ADM-03`, §5.4

Allowed against another administrator — containment, and fully reversible by signing back in.
`SW-ADR-098`

## J-A-04 — A leaver

Deactivate. Confirms: *"Deactivate {email}? They will be signed out immediately and cannot sign
in until reactivated."* Enforced at **three** points: sign-in refused with the **generic** 401 ·
every live session revoked in the same transaction · the request-time check fails closed with
`ACCOUNT_DEACTIVATED` and an explicit message, because identity is already proven mid-session.
`P-ADM-05`

Reactivation **never resurrects revoked sessions.** `P-ADM-05`

**Seam checked:** generic at the login boundary, explicit mid-session. The first reveals nothing
to an attacker; the second stops a legitimate person retrying forever against a door that will
never open. ✅

## J-A-05 — A second administrator

| # | Intent | What happens | Spec |
|---|---|---|---|
| 1 | Promotes someone. | Sessions kept; the new role takes effect on their **next request**, because the role is re-read from the record rather than trusted from a token claim. | `P-ADM-06`, §3.1 |
| 2 | Later demotes them. | **Every session revoked in the same transaction.** | `P-ADM-06` |
| 3 | Tries to demote the last one. | **409.** No sequence of permitted actions may reach zero administrators. | `P-ADM-07` |
| 4 | Tries to deactivate the last one instead. | **409.** The guard covers deactivation too. | `P-ADM-07` |
| 5 | Tries to reset a peer administrator. | **403.** To reset a peer: demote first, then reset — two deliberate, separately audited steps. | `P-ADM-04` |
| 6 | Resets **themselves**. | **Allowed** — with no self-service password change, it is the only password-change route anyone has. | `P-ADM-04`, `P-PRV-06` |

**Seam checked:** step 4 is the one `SRC-001 §4.4` missed. It guarded demotion while deactivation
reached the identical dead end — and with no self-service reset and the bootstrap variable
covering only a *fresh* database, recovery would have been hand-written SQL. ✅

**Seam checked:** step 5. As specified, one administrator could take over another's account in a
single click: the code is shown to the issuer and the target is signed out in the same act. ✅

## J-A-06 — After an incident

Reads the record. Newest first, **rendered as a formatted sentence per action, never a raw JSON
blob** — nobody reads a blob, and a violation inside one is invisible to review. `P-ADM-08`

Nine action types, three of which are **read-audits**: listing people, listing sessions, and
reading the record itself each leave a row. In a system whose privacy rule is specifically about
administrators not looking, looking leaves a mark. `P-PRV-04`

The record **outlives the accounts it describes** — it carries no foreign keys, so a person can be
removed without their history following them. `P-PRV-04`, `SW-ADR-083`

## J-A-07 — What an administrator cannot do

| Attempt | Result | Spec |
|---|---|---|
| See anyone's amounts or descriptions | Impossible — no field can hold one | `P-PRV-02` |
| Open anyone's receipt | Impossible — receipts are owner-only, no administrative path | `P-RCP-02` |
| See anyone's IP or device | Not returned — stored for forensics, absent from the response model | `P-ADM-02` |
| Delete a person | **Does not exist in v1** — no endpoint, no screen, no power | `P-ADM-09` |
| Reach another person's expense by id | **404**, identical to not-found | `P-PRV-03` |

**Seam checked:** the last row. A 403 on an existing record and a 404 on a missing one is a
working oracle — walk the id space and learn which ids are real. It is also what makes sequential
integer ids safe; the two decisions must be reversed together or not at all. ✅

---

## Defects filed from this journey

**None** — same caveat as the person's journey, stated in the same terms: this walk happened
*after* 127 gaps were swept and 38 open rows ruled, so it confirms rather than discovers.

**Where a fresh reader should look hardest**, because this walk could not: no step exercised two
administrators acting on the same account concurrently; nothing tested the audit view's
pagination at volume; and the read-audit rows mean an administrator browsing the record generates
rows in the record they are browsing — that recursion is specified but was not walked.

## Coverage

**Administrator `P-` rows traversed:** `P-ACC-02` · `P-ADM-01`…`P-ADM-09` · `P-PRV-02`,
`P-PRV-03`, `P-PRV-04`, `P-PRV-06`. **Surfaces:** `/admin`, `/admin/audit`.
