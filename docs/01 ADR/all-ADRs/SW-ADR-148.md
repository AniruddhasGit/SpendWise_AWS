# SW-ADR-148 — The settings a person owns: rename, re-password, export, deactivate

> **⚠ AMENDED 2026-08-06 by `SW-ADR-150`.**
> Decision A's *ruling* stands and now covers two controls instead of one: the UI must say
> what it does. What stopped being true is its premise — that leaving **is** deactivation,
> because `SW-ADR-107` allowed nothing else. `CR-001` asked for deletion and named it soft,
> so a **Delete my account** control sits beside Deactivate, and telling them apart in the
> copy is this record's rule doing more work, not less. B's export is unchanged and is what
> the delete flow offers first.

| Field | Value |
|---|---|
| ADR | `SW-ADR-148` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | `SW-ADR-098` (Decision 4's *rationale*, not its ruling — see below) |
| Raised by | Client request, 2026-08-06: *"settings on the sidebar which will have generic options like delete the account, etc."* |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-06 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §4.2` · `SW-ADR-098` · `SW-ADR-103` · `SW-ADR-107` · `SW-ADR-122` |

## Context

The client asked for a settings area with *"generic options like delete the account, etc."*

**`SW-ADR-107` rules that user deletion does not exist in v1**, and its reasoning is not
squeamishness:

> Deleting a person's financial history is the clearest one-way door in the register. […] When
> deletion comes, it arrives as a client-run runbook plus a superseding ADR.

The whole product is built on "the money is the record" — it is why deleting a *category* nulls its
expenses instead of taking them, and why `spendwise_app` holds no `DELETE` on `users` at the
database. A delete button would contradict the schema, not merely a document.

## Decision

**A. "Leave" is DEACTIVATION.** `POST /api/auth/deactivate`: sign-in refused, every session
revoked, the cookie cleared, **every row intact**. An administrator can switch it back on, and
`test_deactivating_keeps_every_row` asserts the four expenses and eight categories survive.

The UI says what it does. It does not say "delete" and then deactivate — that is the lie this
decision exists to avoid, and it is the one a person would only discover by asking for their data
back.

**B. `GET /api/auth/export` is the counterweight.** No deletion, but the record is always
portable: the account, every category, every expense, with `amount_paise` as the exact integer.
Under the same row-level security as every other request, so it cannot return another person's
rows even if the query were wrong.

**C. `PATCH /api/auth/me` changes the display name and nothing else.** Email is absent from the
model deliberately — it is the identity the unique index is built on, changing it is an
account-takeover vector when nothing verifies the new address, and `SW-ADR-012` records that there
is **no email in this stack** to verify with. `extra="ignore"`, so a submitted `email` key is
discarded rather than rejected (the `SW-ADR-130` posture).

**D. `POST /api/auth/password` is a real self-service password change.** Current password
required — without it, anyone holding a live cookie locks the owner out, and a stolen session
becomes a stolen account. It signs out **every other session and not this one**: signing someone
out of the browser they are standing in punishes the action this exists to encourage, and "change
my password" is exactly what a person does when they suspect one of the others is not theirs.

**E. The last active administrator cannot deactivate themselves** — the same guard
`SW-ADR-098 (1)` extends across demotion and deactivation, for the same reason: recovery from zero
active administrators is hand-written SQL.

## What this amends, and what it does not

`SW-ADR-098 (4)` allows an admin to reset their own password, and its stated reason is *"with no
self-service password change, that is the only password-change route anyone has."* **D removes that
premise.** The ruling still stands and is implemented — it was made one tier above this session and
this record does not touch it — but its rationale is now historical, and a future reader comparing
the two should know which sentence stopped being true and when.

## Consequences

- `password_resets` finally has a redemption path. The table, the hash column and
  `SW-ADR-032`'s "store the hash, never the token" existed since the baseline migration with no
  endpoint able to redeem one.
- `POST /api/auth/reset/complete` is **unauthenticated by definition** — the point of a reset is
  that the person cannot sign in — which meant it opened a session with no `app.user_id`, and the
  revocation it performs matched zero rows under RLS. It now sets the identity from the redeemed
  token's row before touching `sessions`: possession of the token *is* the proof of identity this
  endpoint accepts, and it has just been checked.
- Four states on redemption — unknown, expired, already used, valid — return **one message** for
  the first three. Telling an attacker which one they hit turns a guessed token into an oracle.

---

*Ruled under `SW-ADR-015`.*
