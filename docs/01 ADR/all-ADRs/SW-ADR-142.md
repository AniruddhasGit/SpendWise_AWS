# SW-ADR-142 — The spec of record gets checked against the documents it cites

| Field | Value |
|---|---|
| ADR | `SW-ADR-142` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice run 5 |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-138` · `SW-ADR-140` · `SW-ADR-141` · `SRC-001` ERRATUM E-6 · Art II.1 |

## Context

The fifth uncoached slice logged eight guesses and listed **thirty** candidates it had checked and
deliberately not logged. The document set is closing. But every remaining defect it found was
**inside `contract.json`** — the spec of record itself — and each had the same shape: *a
hand-written cell asserting something about another document, where the assertion was never
checked against that document.*

**1. It contradicted the frozen source, on the strength of a misreading.** The seed block created
a **third** person, an ADMIN account, justified in its own `why` cell as *"`P-ACC-02` refuses to
start with zero admins."* `P-ACC-02` actually reads: *"If no administrator exists **and the
variable is unset**, the application refuses to start."* Setting the variable with zero
administrators starts perfectly well.

On that misreading the block overrode `SRC-001` **ERRATUM E-6** — *"two users seeded"* — plus
`CONSTITUTION.md` Art IX.4 and the binary criterion Bible `E0-S4 AC1` (*"exactly 2 people"*).
**That is the top of the authority order overridden by a document one level below it**, which is
the failure Art II.1 exists to prevent, committed in the artifact meant to end such failures.

**2. `Principal` drifted in the same commit that added it.** `SW-ADR-141` put `Principal` into
the spec of record *because an undefined model drifts*. It was written without opening `P-ACC-06`,
the one specification it models, and omitted `receipts_enabled` — which `P-ACC-06`, Bible `E1-S8`,
`SIT-E1-S8-02`, `SIT-E5-S3-01`, `P-RCP-03` and `08_failure_modes.md` all require.

**3. `amount.scale` was unreachable dead text.** The grammar pattern capped the fraction at two
digits and was ordered *before* `amount.scale`, so `12.345` returned *"Amount must be a decimal
string"* — never the sentence `P-REC-01` quotes. In a registry whose own note says *"the rendered
sentence is what a test asserts on."*

**4. Seventeen models were named and none defined.** The route table referenced `ExpensePage`,
`Category`, `RegisterRequest`, `AdminUser` and thirteen more. `SW-ADR-141` defined exactly three
and stopped — which is, word for word, the failure its own note describes about the eleven value
rules that got messages while `field.required` and `field.type` did not.

## Decision

**A. `consistency_check.py` gains `contract-refs`.** Every route's `request_model` and
`response_model` must resolve to a defined model, and every `P-` row and Bible story id named
anywhere in `contract.json` must resolve. **This one check catches defects 2 and 4 today.**

> The generator proved `contract.json → PRD` in one direction. **Nothing proved
> `contract.json → the documents contract.json cites.`** That asymmetry is the whole finding.

**B. The seed creates exactly TWO people**, per `SRC-001` E-6. `BOOTSTRAP_ADMIN_EMAIL` is set in
the gate environment to an address **nobody registers** — which is what `P-ACC-02` requires.

**C. All seventeen models are defined**, request and response. `AdminUser` carries
`expense_count` and `last_activity` from `admin_expense_stats()` and **no field capable of holding
an amount** — the `P-PRV-02` control, expressed as a type.

**D. `Principal` carries `receipts_enabled`.**

**E. The amount grammar checks shape, not scale.** `^-?[0-9]{1,15}(\.[0-9]+)?$` — any number of
decimals; `amount.scale` counts them and owns `P-REC-01`'s sentence.

**F. `REPEATABLE READ` on any request that reads the summary.** `SRC-001 §7.4` asked for one
round trip; `SW-ADR-017` split it into three queries and nothing re-established atomicity. Under
`READ COMMITTED` each statement takes a new snapshot, so a concurrent insert between the headline
and the breakdown breaks *"the breakdown sums exactly to the headline total"* — asserted
unqualified by `P-UND-05`, `06_summary_sequence.md`, `SIT-E0-S9-04` and `SIT-E2-S5-03`.
**Invisible in every single-user test; it fails only in production, intermittently, on the one
number the product is about.**

**G. Person B's two expenses are in the fixture.** Bible `E0-S7 AC6` — *"as B, the list returns
exactly B's seeded count"* — had **no expected value**, so it could not be written as a failing
test first, which Art IX.1 requires.

**H.** `field.required` is scoped to body keys and `range.required` to the summary's query pair,
so neither is unreachable. Explicit `null` on a required field is `field.required`. Plus `CV-21`
(the grammar owns every non-conforming amount), `CV-22` (a non-empty description is stored
verbatim), `CV-23` (calendar arithmetic at the year boundary), and the span cap as a formula.

## Consequences

- **A spec of record is a document, and documents drift.** It earns its name from being *checked*,
  not from being called one. `contract.json` closed sixteen questions for the fifth reader and
  was the source of every defect that reader still found.
- The rule generalises: **a `why` cell that paraphrases another document is a citation**, and
  citations get checked. The misreading of `P-ACC-02` would have been caught by a human opening
  the file; nothing in the pipeline opened it.
- Five uncoached runs, in order: **18 → 21 → 15 → 8 → 8**. The count has stopped falling, and the
  findings have moved from *the whole document set* to *one file*. That is what closing looks
  like — and the residue is now reviewable by reading a single artifact.

---

*Ruled under `SW-ADR-015`. It supersedes nothing.*
