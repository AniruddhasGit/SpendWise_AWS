# Engineering ledger — column dictionary

**The ledger is DERIVED from the Bible.** If the two disagree, the Bible wins and
`generate_ledger.py` is re-run. Editing a derived column by hand is erased by the next run,
silently — the same trap `SW-ADR-066` names for the data-model package.

**During the build, exactly one column is hand-edited: `Status`.**

| Column | Meaning | Written by |
|---|---|---|
| `Type`, `ID`, `ParentID`, `Title` | identity, from the Bible | generator |
| `AcceptanceCriteria` | the binary criteria, verbatim | generator |
| `Priority`, `Estimate`, `Milestone` | from the Bible | generator |
| **`Status`** | `Backlog` → `In Progress` → `Done` / `Blocked` | **the building session, by hand** |
| `DependsOn` | one story id, real | generator |
| `Labels`, `Persona` | routing hints | generator |
| **`OwnedPaths`** | **the write-set — the exact paths this story may touch** | generator |
| `Wave` | stories that may run together | generator |
| `TestTrustLevel` | what evidence closes it: `gate-observed` · `db-verified` · `browser` · `red-proof` · `api` | generator |
| `SITCaseIDs` | the positive cases that prove it | generator |
| `NegativeCaseIDs` | the negative suite that attacks it | generator |
| `EvidencePath` | where the observed output is filed | generator |
| `SourceRef` | the `P-` row or ADR it implements | generator |

## Two columns are load-bearing for `/ss`

**`Milestone` and `Status`, by those exact names.** The `SessionStart` hook discovers a ledger by
scanning for a delimited file whose header carries both. Rename either and a cold session silently
loses its frontier — it will not error, it will simply report `N/A` and orient from git alone.

**Verified, not assumed.** The hook was run against this file and returned:

```
Engineering ledger — milestone × status (docs\10 EngineeringLedger\engineering_ledger.tsv)
M0: 10 Backlog   M1: 7   M2: 7   M3: 8   M4: 5   M5: 3   M6: 4
Lowest milestone with non-Done rows: M0
```

## `OwnedPaths` — what makes parallel work safe

**Two stories whose `OwnedPaths` overlap must never run at the same time.** Grouping by *topic*
is not good enough: on the project this method came from, work packed by topic put five pairs of
tasks onto the same file.

The generator asserts this and reports `write-set clashes`. Today: none — every same-wave pair is
dependency-ordered, so nothing can collide.

## Integrity, computed on every run

```
stories written        : 44
unresolved DependsOn   : none
dependency cycles      : none
write-set clashes      : none
header carries Milestone+Status : YES
```

**Determinism:** running the generator twice produces a byte-identical file — both runs hashed
`c15a03b5d04e035e`. A generator that is not deterministic makes every diff unreadable and every
drift check meaningless.
