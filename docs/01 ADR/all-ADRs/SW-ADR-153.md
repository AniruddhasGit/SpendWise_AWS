# SW-ADR-153 — `E6-S5` is narrowed to match the capabilities the client actually approved

| Field | Value |
|---|---|
| ADR | `SW-ADR-153` |
| Pack | `SPENDWISE_V1` |
| Type | SCOPE_CORRECTION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instruction 2026-08-21 |
| Decision date | 2026-08-21 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Amends | `E6-S5` in `docs/05 Bible/SpendWise_Bible.csv` · `SIT-E6-S5-01`, `-02` |
| Sources | `SW-ADR-148` · `SW-ADR-150` · `CR-001` · `CONSTITUTION.md` Art II.6 · the finding in `docs/12 DesignReview/` |

## Context

`E6-S5` — *"Capabilities that must NOT exist"* — was written during `GOAL_07`, before the
capabilities it forbids were approved. Two of its four acceptance criteria had since become false
of the shipped product, and **the falsity was itself approved**:

| Criterion clause | Reality | Sanctioned by |
|---|---|---|
| no self-service **email** change | still absent | — clause holds |
| no self-service **display name** change | `PATCH /api/auth/me` exists | `SW-ADR-148` **C** |
| no self-service **password** change | `POST /api/auth/password` exists | `SW-ADR-148` **D** |
| no route deletes a user | `DELETE /api/auth/me` exists but is **soft** | `SW-ADR-150`, `CR-001` |

The code was never wrong. The Bible row predated `SW-ADR-148` (`8e75a4c`) and `SW-ADR-150`
(`4e7867b`) and was never reconciled, leaving an unmarked contradiction between two live documents
— which `CONSTITUTION.md` Art II.6 calls a defect rather than a reader's judgement call. Three SIT
cases were written to assert that the product does not do something it was deliberately built to
do.

## Options considered

- **A.** Narrow the criteria to match the approved capabilities. No code changes.
- **B.** Treat the criteria as authoritative and delete self-service rename and password change.
- **C.** A partial reversal — keep one capability, drop the other.

## Decision

**A**, ruled by the client on 2026-08-21 in response to a plain-language summary of all three
options and their costs.

The build session did **not** decide this. It raised the contradiction, recorded it as `OPEN`, set
`E6-S5` to `Blocked`, and stopped — because rewriting an acceptance criterion changes what "done"
means, which `CLAUDE.md` reserves at any confidence. A, B and C describe three different products.
Choosing A unilaterally would have been editing the definition of done to match what had already
been built, which is the precise failure the status law exists to prevent.

## The new criteria

Clause count is deliberately unchanged at four, so `SIT-E6-S5-01..04` keep their identifiers and
nothing downstream renumbers.

1. no route, handler or CLI path **hard-deletes** a user — asserted by walking the route table and
   by the absence of a `DELETE` grant on `users`; `DELETE /api/auth/me` is **soft**
   (`SW-ADR-150`) and every row survives
2. no endpoint lets a person change their own **email** (`SW-ADR-148` C narrowed this clause:
   display name and password are self-service by design)
3. both absences are proved by a NEGATIVE test that fails if the capability ever appears
4. (a specification that something does not exist still needs a test, or it silently arrives later)

**Clause 1 changed method, not substance.** The original asked for "grepping for a delete-user
operation", which finds `delete_me` and fails against correct code. What it was reaching for is
that no row is ever destroyed — so the test now asserts the grant (`spendwise_app` holds no
`DELETE` on `users`, `security.sql:267`) and the soft semantics, which is the property that
actually protects the data.

**Clause 2 lost two thirds of its scope and kept the third that matters most.** Email is the
identity the unique index is built on; changing it with nothing to verify the new address is an
account-takeover vector, and `SW-ADR-012` records that there is no email in this stack to verify
with. That clause was always the load-bearing one.

## Why

The alternative to narrowing was deleting shipped, approved capability to satisfy text older than
the approval. `SRC-001 §4.2` is not the authority being overridden here — `SW-ADR-148` already
ruled on these capabilities with the client's delegation, and `CR-001` is the client's own
instruction for soft delete. The Bible is the scope arbiter, so it is the Bible that has to move
for the arbiter and the product to agree again.

## Also corrected

`ADR_DECISION_RELEASE_LEDGER.tsv` recorded `SW-ADR-148` as `included_in_bible = INCLUDED`. **No
story in the Bible cites it** — there is no row for `PATCH /api/auth/me`, self-service password
change, `DELETE /api/auth/me`, or `GET /api/auth/export`. The cell is corrected to
`NOT_INCLUDED`, which is true, rather than left as a claim the artifacts do not support.

**Four shipped features still have no Bible story.** That is a real coverage gap, recorded here
and NOT closed by this record: authoring four new stories is itself a scope change and is the
client's to ask for. It is carried forward rather than quietly fixed.

## Consequences

- `E6-S5` moves from `Blocked` to buildable; nothing in `app/` changes.
- `SIT-E6-S5-01` and `-02` are rewritten to the new text; `-03` and `-04` are unchanged.
- The finding in `docs/12 DesignReview/` is marked RESOLVED with a pointer here.

## Reversibility

Yes — a superseding record restoring the original clauses, which would then require deleting
`PATCH /api/auth/me` and `POST /api/auth/password`. That is option B, and it remains available.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file.*
