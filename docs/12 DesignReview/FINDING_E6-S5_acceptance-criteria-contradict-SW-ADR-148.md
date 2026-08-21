# FINDING — `E6-S5`'s acceptance criteria contradict shipped, approved behaviour

| | |
|---|---|
| Found | 2026-08-21, while preparing to build `E6-S5` |
| Status | **RESOLVED 2026-08-21 — the client ruled option A. See `SW-ADR-153`.** |
| Blocks | nothing. `E6-S5` was `Blocked`; unblocked by the ruling. |
| Class | `CONSTITUTION.md` Art II.6 — an unmarked contradiction between two live documents |

## The contradiction

`E6-S5` — *"Capabilities that must NOT exist"* — carries this acceptance criterion, in both
`docs/05 Bible/SpendWise_Bible.csv` and `docs/10 EngineeringLedger/engineering_ledger.tsv`:

> no endpoint lets a person change their own email, display name or password

Two thirds of that is false of the shipped product, and **the falsity is approved**:

| Capability | Exists? | Sanctioned by |
|---|---|---|
| change own **email** | no | — criterion holds |
| change own **display name** | **yes** — `PATCH /api/auth/me` | `SW-ADR-148` **C**, APPROVED / RELEASED |
| change own **password** | **yes** — `POST /api/auth/password` | `SW-ADR-148` **D**, APPROVED / RELEASED |

`SW-ADR-148` says so in as many words:

> **C. `PATCH /api/auth/me` changes the display name and nothing else.**
>
> **D. `POST /api/auth/password` is a real self-service password change.** Current password
> required … It signs out every other session and not this one.

A second criterion is **narrowed rather than contradicted**:

> no route, handler or CLI path deletes a user — asserted by walking the route table and grepping
> for a delete-user operation

`DELETE /api/auth/me` now exists (`CR-001`, `SW-ADR-150`). Its *substance* still satisfies the
criterion — deletion is SOFT, every row survives, and `spendwise_app` holds no `DELETE` grant on
`users` (`docs/06 DataModel/security.sql:267`), so hard deletion remains impossible at the
database for the runtime role. But the criterion's own stated **method** — "grepping for a
delete-user operation" — finds `delete_me` and `DELETE /api/auth/me` and, written literally, fails
against correct code.

## Why this is not a code defect

Nothing here is rogue. Every capability that appears to violate the criterion traces to an
APPROVED, RELEASED ADR decided under `SW-ADR-015`. The code is right.

**The documents are wrong, and unmarked.** `CONSTITUTION.md` Art II.6:

> An unmarked contradiction between two live documents is a defect, not a reader's judgement call.

The Bible row predates both ADRs and was never reconciled. Confirmed from git: the Bible was
written in `71ff1e4` (GOAL_07); `SW-ADR-148` landed later in `8e75a4c`; `SW-ADR-150` later still in
`4e7867b`. Neither the Bible row, the ledger row, nor SIT cases `SIT-E6-S5-01..04` (still `NotRun`)
have been touched since.

**Three SIT cases are currently written to assert that the product does not do something it was
deliberately built to do.** Run as written, they fail against correct code — and the obvious
"fix" is to change the code back, which would delete an approved feature to satisfy stale text.

## A second, smaller drift found alongside it

`docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv` records `SW-ADR-148` with
`included_in_bible = INCLUDED`. **No story in `SpendWise_Bible.csv` cites `SW-ADR-148`** — there is
no Bible row for `PATCH /api/auth/me`, for self-service password change, for `DELETE /api/auth/me`,
or for `GET /api/auth/export`. The ledger claim is not true of the artifacts.

`SW-ADR-150` records `included_in_bible = NOT_INCLUDED`, which is correct.

## Why the build session stopped instead of fixing it

`CLAUDE.md` reserves, at any confidence: **"what the product is and what 'done' means · scope
changes."** Rewriting an acceptance criterion is a scope change. Three resolutions are available
and they are materially different products:

- **A.** The criterion is stale. Amend it to *"no endpoint lets a person change their own
  **email**"*, and restate criterion 1 as *"no route hard-deletes a user; `DELETE /api/auth/me` is
  soft and every row survives"*. Nothing in the code changes. **Most likely correct** — it matches
  the approved ADR chain and the client's own `CR-001` instruction.
- **B.** The criterion is right and `SW-ADR-148` was a mistake. Remove self-service rename and
  password change. This deletes shipped, approved capability.
- **C.** Something between — e.g. keep password change, drop rename.

The build session believes **A** and has not applied it. Under `SW-ADR-015` a reversible reserved
matter may be decided and batched for reversal, but this one changes what the product *is*, and
the honesty floor's "a gap stays a gap" applies more cleanly than its delegation clause.

## What can be honestly tested today, if a partial `E6-S5` is wanted

- no hard-delete path: no `DELETE` grant on `users`, no CLI back door in `tools/`, no runtime
  hard-delete route — **testable now, and true**
- the email-change absence — **testable now, and true**

Those two would be real coverage. They would **not** make `E6-S5` Done, because a story is done
when its acceptance criteria pass, and two of its clauses currently cannot.

## Recommended next step

Rule between A, B and C. If A, the edit touches `SpendWise_Bible.csv`, the regenerated
`engineering_ledger.tsv`, `SIT-E6-S5-01..04`, and wants a superseding note recording that
`SW-ADR-148` and `SW-ADR-150` narrowed this story after it was written — plus a correction to
`SW-ADR-148`'s `included_in_bible` cell, or a Bible story that makes it true.
