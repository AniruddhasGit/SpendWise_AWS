# SW-ADR-150 — Deletion arrives, and it is SOFT: every row kept, the address kept, restorable by an administrator

| Field | Value |
|---|---|
| ADR | `SW-ADR-150` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-107` (user deletion does not exist in v1) |
| Amends | `SW-ADR-148` (Decision A — leaving is no longer *only* deactivation) |
| Raised by | `CR-001`, the client, 2026-08-06: *"the user must be able to delete their account and the account will be soft deleted from the DB"* |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-06 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CR-001` · `SRC-001 §6.9` · `SW-ADR-097` · `SW-ADR-098` · `SW-ADR-100` · `SW-ADR-107` · `SW-ADR-148` |

## Context

`SW-ADR-107` ruled that user deletion does not exist in v1 — *"No endpoint, no screen, no admin
power, no seed-script back door"* — and `SW-ADR-148 A` built the settings area on top of it:
leaving is deactivation plus an export, and the control says what it does rather than saying
"delete" and doing something else.

Neither record closed the question. `SW-ADR-107` named, in its own text, the exact terms on which
it would reopen:

> Deleting a person's financial history is the clearest one-way door in the register. […] When
> deletion comes, it arrives as a client-run runbook plus a superseding ADR.

The client has now asked for deletion and named its form in the same sentence: *"the account will
be soft deleted from the DB"*. **Soft is the version that does not walk through the door
`SW-ADR-107` was standing in front of.** Nothing is destroyed, so nothing is irreversible, so the
stated reason for the ruling is *discharged*, not overruled. `CR-001` is the client instruction
`SW-ADR-107` asked for; this record is the superseding ADR it asked for. Both halves are present,
which is why this is a supersession rather than a build session quietly deciding it knew better.

The reason to be precise about that: `SW-ADR-107`'s ruling was never "deletion is wrong". It was
"a one-way door needs an authority above this session to open it." That sentence is still true and
this record does not touch it. What changed is that the client asked for a door that swings both
ways.

## Decision

**A. Deletion is SOFT. One nullable column, and every row survives.**

`DELETE /api/auth/me` sets `deleted_at = now()` **and** `is_active = false`, and revokes every
session, all in one transaction. Every expense, every category, every audit row and the person
record itself are left exactly as they were. That is the same guarantee `SW-ADR-148 A` made for
deactivation — `test_deactivating_keeps_every_row` asserts it — now made for the control that
says *delete* on the tin. An administrator can put the account back.

`deleted_at TIMESTAMPTZ NULL`, and it is a timestamp rather than a boolean on purpose. A boolean
tells you an account was closed; a timestamp tells you **when**, which is the question an
administrator restoring one actually has, and the question no `is_deleted` column can be made to
answer later without a migration and a guess. `NULL` means live, so the common case needs no
predicate at all — and a query that forgets the column therefore fails **open**, returning a live
account it was always meant to return, rather than hiding a live person from a lookup that has no
other way to find them.

`is_active` is set alongside it, and that is not belt-and-braces. Every `is_active`-shaped guard
already in this system — `count_active_admins`, the admin overview's account counts,
`set_active`'s last-admin check — would otherwise read a closed account as a live one, and the
first symptom would be a lockout nobody could explain.

**B. The unique index on `lower(email)` stays TOTAL. A closed account keeps its address.**

While the closed row exists, that address cannot be registered again.

The rejected alternative was a **partial** unique index — `… WHERE deleted_at IS NULL` — which
lets a person return under the same address. It reads as the kinder option and it is the more
expensive one. It creates **two rows carrying one address**, and from that moment every lookup in
this system that starts from an email — sign-in, the administrator's search, a password reset, and
whatever support path is written a year from now by someone who was not here — must disambiguate
them **correctly, forever**. The failure mode when one of them does not is being signed in as the
wrong person. And there is no floor under that mistake: `users` sits **outside row-level security**
by `SW-ADR-097`, because a policy keyed on the request identity cannot serve a lookup that happens
before there is one. One address, one row: the constraint does the disambiguating once, at the
database, where it cannot be forgotten.

The person who wants to come back is not stranded — an administrator restores the account. That is
**one** action, not two: `POST /api/admin/users/{id}/active` with `is_active: true` on a closed
account clears `deleted_at` as well. Restoring in two steps is restoring that can be left
half-done, and the half-done state is an account that is active and still reads as deleted.

**C. Deactivate and delete BOTH remain, and they remain distinct.**

They do nearly the same thing to the database and they are not duplicates, because the duplication
is in the schema and the difference is in the person. Deactivate is *"pause me"*; delete is
*"close it"*. Someone stepping away for three months and someone who has decided to leave are
asking for different things, and a product that offers only one of the two words forces one of
them to say something they do not mean.

Collapsing them would have to be done in one of two directions and both are worse. Drop deactivate,
and the admin loses the containment tool `SW-ADR-100` exists to provide — you cannot suspend a
suspicious account without recording that it *left*. Drop delete and keep deactivate under a
"Delete my account" label, and you are back to the precise lie `SW-ADR-148 A` was written to
prevent: the one a person only discovers when they ask for their data back.

So both stay, and the copy carries the weight. The confirmation must say what actually happens —
the account closes, sign-in is refused, **the records are retained and an administrator can restore
it**, and the email address stays taken — and it offers the `SW-ADR-148 B` export first. A person
who reads "delete" and expects erasure has been misled by omission, even though every fact in this
record is defensible.

**D. The last active administrator cannot delete themselves — `409`, `field: "is_active"`.**

The same guard as `SW-ADR-098 (1)`, and deliberately the same *code and field* as
`deactivate_self`, because it is the same failure: a system with zero active administrators, whose
recovery is hand-written SQL against production. `SW-ADR-098 (1)` extended the guard from demotion
to "**every** action that would leave zero active admins"; a third such action arriving is exactly
the case that wording anticipated, so this is an application of that ruling and not a new one.

The check runs **first**, before any column is touched, so a refused delete leaves the row exactly
as it found it.

**E. Sign-in is refused with the generic 401; a live session is refused with `ACCOUNT_DEACTIVATED`.**

`SW-ADR-100 (1)` is unchanged and is what a closed account inherits: login fails with the same
generic 401 (`SESSION_INVALID`) as a wrong password, bcrypt compare still run. Nothing
pre-authentication may reveal that an address belongs to a closed account rather than to nobody —
that is an account-existence oracle, and it is worth more to an attacker here than elsewhere
because the address is *still taken* under **B**.

An in-flight session is a different situation and gets a different answer: `principal_for` refuses
it with `ACCOUNT_DEACTIVATED` and the same message deactivation uses. The person is already
identified there, so there is nothing left to protect by being vague, and `SW-ADR-100`'s posture is
that explicit mid-session is the honest half of the same rule.

**F. The repository returns closed rows; the SERVICE decides.**

`UserRepository.by_email` and `.by_id` do **not** filter on `deleted_at`. Pushing the filter down
to the repository looks like defence in depth and is the opposite: the administrator has to be able
to find someone who has left — that is the whole of the restore path — and a repository that
cannot return the row makes the capability unimplementable without a second, unfiltered accessor
that then becomes the one everybody uses. One accessor, one truth, and the policy decision stays
where it can be read: in the service, next to the 401 it produces.

## Consequences

- **`SW-ADR-148 A` is amended, not contradicted.** Its ruling — that the UI must say what it does
  — is now *more* load-bearing, not less, because there are two controls to tell apart. What
  stopped being true is its framing that leaving *is* deactivation; leaving now has two shapes.
  `SW-ADR-148 B`'s export is unchanged and becomes the thing offered immediately before a person
  closes the account.
- **`spendwise_app` still holds no `DELETE` on `users`.** The grant in `security.sql` is unchanged,
  and that is the point: this record adds a capability the application can exercise without adding
  a privilege it could misuse. Soft deletion is an `UPDATE`. Hard deletion remains impossible at
  the database for the runtime role, which is the guarantee `SW-ADR-107` actually bought.
- **`SRC-001 §6.9`'s cascade semantics still stand and are still unexercised.** `SW-ADR-107` kept
  them as schema-level correctness for a deliberate future deletion, and they stay that way. This
  record does not fire them.
- **The closed account is still counted, and that is a reporting decision with consequences.** It
  is not active, so it does not inflate `accounts_active`; it is still a row, so `accounts_total`
  includes it, and an administrator listing accounts sees closed ones **by default** — because an
  administrator looking for someone who has left has to be able to find them.
- **The trap this leaves for the next person.** `deleted_at` is a second closed-state column beside
  `is_active`, and two columns describing one state drift. Every path that closes an account must
  set both, every path that reopens one must clear both, and the sign-in check tests both
  separately rather than trusting one to imply the other — because a future reactivation path that
  clears `is_active` and forgets `deleted_at` would produce an account that can sign in and still
  reads as deleted everywhere else.

---

*Ruled under `SW-ADR-015`.*
