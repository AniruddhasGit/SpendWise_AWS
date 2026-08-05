# CR-001 — Account deletion, and an administrator who can see spending over time

| Field | Value |
|---|---|
| Change request | `CR-001` |
| Raised by | **The client**, 2026-08-06, verbatim below |
| Status | **ACCEPTED** — implemented under `SW-ADR-150`, `SW-ADR-151` |
| Reverses | `SRC-001 §4.2` (the admin row of the permission matrix) · `SW-ADR-107` (no user deletion in v1) |
| Amends | `SW-ADR-129` · `SW-ADR-148` |

## What was asked for

> yeah i know what the docs say i think we need to make changes as this is new requirement. the
> user must be able to delete their account and the account will be soft deleted from the DB. The
> admin will be able to see all the users graphs when they open a particular user from a list. they
> will be able to search any user with their detilas like email id, name. also they can see the
> expenses that are happening not the categories spent on so the will be able to see the line plot
> for that particular user and have the filter option to see the line plot based on time filter.

## Corrections to this file, made after it was written

Recorded rather than silently patched, because a change request that quietly edits its own
premises is worth less than one that shows them.

1. **The matrix row was misquoted.** It was reproduced here without `(see §4.5)`. That pointer is
   not decoration: §4.5 is the privacy value the whole `SW-ADR-129` mechanism was built to make
   true, and it is the clause this request's own argument leans on. Restored below.
2. **`Amends: SW-ADR-149` was wrong.** `admin_user_daily()` *inherits* `SW-ADR-149`'s identity
   swap unchanged — nothing about that record changes — and declaring an amendment would have
   forced a banner onto it announcing a change that never happened. Removed; `SW-ADR-151` cites it
   as a source instead.
3. **`CR-001_CONTRACT.md` did not warn its workers that superseding `SW-ADR-107` flips its ledger
   status**, which turns every live citation of it into a build failure. Four such citations were
   in flight when the supersession landed. That omission is a fault of the contract, not of the
   workers who hit it.

## Why this is a change request and not a bug fix

Two frozen positions are being reversed, both deliberately taken and both recorded:

**1. `SRC-001 §4.2`** — the client's own permission matrix, in their own words:

> | | user | admin |
> |---|---|---|
> | See anyone else's expense amounts | no | **no** (see §4.5) |

The bold **no** was theirs. `SW-ADR-129` built the whole admin data path around it: a
`SECURITY DEFINER` function returning two columns, so "how much" was unanswerable *at the
database* rather than merely absent from a response model.

**2. `SW-ADR-107`** — no user deletion in v1, now superseded by `SW-ADR-150`:

> Deleting a person's financial history is the clearest one-way door in the register. […] When
> deletion comes, it arrives as a client-run runbook plus a superseding ADR.

The client has now asked for deletion and named its form — **soft** — which is the version that
does not walk through that door. `SW-ADR-107`'s own text anticipated this arrival, and it is
superseded by `SW-ADR-150` on exactly the terms it named. It is no longer authority; its ledger
row reads `SUPERSEDED` and its text keeps its banner.

`SRC-001` is frozen and fingerprinted (`consistency_check.py` fails on an edit), so neither clause
can be struck where it stands. This file is the record instead, and the two ADRs below carry the
implementation.

## What was granted, and what was deliberately not

The request draws a specific line — *"the expenses that are happening **not the categories spent
on**"* — and that line is the whole design.

| An administrator may now | An administrator still may not |
|---|---|
| see a person's **total** over a range | see **which categories** they spend in |
| see the **daily line plot** of that spending | see any **description** on any expense |
| filter it by time | see an individual expense row |
| see counts, dates, sessions, audit | see a category breakdown, at any granularity |

Category and description remain unreadable, and remain unreadable **structurally**: the new
function's `RETURNS TABLE` clause declares `day`, `total_paise` and `entries`, and there is no
column for anything else. That is the same mechanism `SW-ADR-129` established, pointed at a line
the client has moved rather than abandoned.

## Consequences the client should know about

- **A soft-deleted account keeps its email address.** The unique index on `lower(email)` stays
  total, so the same address cannot register again while the deleted row exists. The alternative —
  a partial index — lets a person return under the same address and creates two rows with one
  address, which every lookup would then have to disambiguate correctly, forever. An administrator
  can restore the account instead.
- **An administrator can now see how much a person spends.** That is the point of the change, and
  it is worth stating plainly: it is a reduction in privacy that was previously ruled out, taken
  deliberately, and every read of it is written to the audit log.

---

*Accepted under `SW-ADR-015`. Implemented by `SW-ADR-150` (deletion) and `SW-ADR-151` (admin
spending visibility).*
