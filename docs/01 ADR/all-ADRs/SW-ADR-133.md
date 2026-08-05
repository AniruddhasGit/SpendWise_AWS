# SW-ADR-133 — Erratum: Constitution counts refreshed to repository state; no rule changed

| Field | Value |
|---|---|
| ADR | `SW-ADR-133` |
| Pack | `SPENDWISE_V1` |
| Type | GOVERNANCE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 exit gate, X-01 FINDING-4 and FINDING-5 |
| Decided by | **FABLE_5** (escalation tier, under the client's standing instruction) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | Art II.6 · Art XI.1 · Preamble · Fable 5 adjudication, 2026-08-05 |

## Context

`CONSTITUTION.md` states three arithmetic snapshots taken on drafting day: Art I.1 "the **22
records** in `docs/01 ADR/all-ADRs/`", Art II.3 "**Seven** exist (`E-1`…`E-7`)", Art III.3 "All 22
rows read `NOT_INCLUDED` today… those documents do not yet exist". The repository now holds **132**
records, **ten** errata, and documents `02`–`11` all exist and are populated.

Read literally, Art I.1 — the **scope** article — puts 110 of the 132 records outside the
functional envelope, including every ruling the PRD is built from, making the entire PRD scope
creep. Art III.3 asserts as present fact something that stopped being true eleven documents ago.

Amending `CONSTITUTION.md` is **reserved**. So the question was escalated: is refreshing a stale
count an amendment?

## Decision

**It is an erratum, not an amendment, and Art II.6 requires it** — an unmarked contradiction
between two live documents is a defect.

The figures were arithmetic snapshots, not rules. Art I.1's rule is **location-based**; Art XI.1
already settles the tie ("for decision status, trust the ledger… never a path quoted in prose"),
so the literal reading inverts the Constitution's own reading rule. Every record that entered that
location did so by a client-authorised mechanism: `SW-ADR-015` delegation, the client's verbatim
escalation instruction executed at this tier, and Art III.2 superseding records. Refreshing the
count moves no envelope; it makes the description match the envelope those mechanisms already
lawfully produced. The document is `v0.1-draft`, **UNADOPTED** — there is no ratified text to
amend, and putting a signature block above known-false arithmetic would itself breach Art VII.1.

**No version bump.** `spendwise-constitution@0.1.0` is stamped in the BRD and PRD and Art XII.3
makes stamp drift catastrophic; the bump is the *amendment* mechanism, and this is not one.

**Art I.1 is restated as location-plus-ledger** rather than a number, which retires this staleness
class permanently instead of resetting its clock.

**The boundary, stated hard:** this classification holds **only** because no normative sentence
changes — no `MUST`, no `MUST NOT`, no article's operative meaning. The instant a refresh would
alter what any rule requires, it is an Article XII amendment and the build session stops.

## Consequences

- The header's "Drafted 2026-08-05, from… the 22 records" is **not** touched. It is a true
  historical statement about the drafting, and rewriting it would destroy a fact to fix a count.
- Each touched clause carries a dated citation, so the edit is loud rather than silent.
- **Flagged for the client digest** under `SW-ADR-015`: reversible in one message.
- If the client rules that count refreshes *are* amendments, the stale figures must still be
  **marked** stale in place with a pointer to the ledger — Art II.6 forbids the unmarked
  contradiction either way.

---

*Ruled at the Fable 5 escalation tier. A recording ADR: it supersedes nothing.*
