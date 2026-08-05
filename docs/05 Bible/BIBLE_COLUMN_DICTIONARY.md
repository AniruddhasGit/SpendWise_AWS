# Bible — column dictionary

`SpendWise_Bible.csv` is the **scope arbiter**. After this document, no scope exists beyond an
`AcceptanceCriteria` cell.

| Column | Meaning | Who writes it |
|---|---|---|
| `Type` | `Epic` or `Story` | author |
| `ID` | `E{n}` or `E{n}-S{m}` | author |
| `ParentID` | the epic a story belongs to | author |
| `Title` | what it is, in a line | author |
| `Description` | why it exists, where it is not obvious | author |
| **`AcceptanceCriteria`** | **pipe-separated, every one binary** | author |
| `Priority` | `P0` blocks the milestone · `P1` does not | author |
| `Estimate` | rough points; calibration only, never a commitment | author |
| `Milestone` | `M0`…`M6` | author |
| `Labels` | semicolon-separated | author |
| `Status` | `Backlog` → `In Progress` → `Done` / `Blocked`. **The only column edited during the build.** | the building session |
| `DependsOn` | one story id. Real, not decorative. | author |
| `SourceRef` | the `P-` row(s) or ADR this implements | author |

## The rule about acceptance criteria

**Every criterion must be checkable by running something.** These fail and would be sent back:

- ~~"The dashboard works"~~ — nothing to run
- ~~"Isolation is enforced"~~ — enforced how, observed where?
- ~~"Performance is acceptable"~~ — by whose measure?

These pass:

- "as the RUNTIME role with `app.user_id` set to B, `SELECT * FROM expenses WHERE id = {A's id}` returns ZERO rows"
- "`GET /api/expenses/summary?from=2026-08-01&to=2026-08-31` with today mocked to 2026-08-05 returns `daily_average_paise = 75810`"
- "the 11th sign-in attempt in a minute from one IP returns 429 with a `Retry-After` header"

**A story whose criteria cannot be turned into a failing test is not a story yet — split it.**

## Milestones

| | | Stories |
|---|---|---|
| `M0` | **The spine and the day-one proof.** Never waivable. Its last story is the evidence record. | 10 |
| `M1` | Accounts, sessions, recovery, the error envelope | 7 |
| `M2` | Categories, expenses, the summary — the thing the app actually does | 7 |
| `M3` | The dashboard | 8 |
| `M4` | Administration | 5 |
| `M5` | Receipts | 3 |
| `M6` | Hardening — prove the checks can fail | 4 |

**`M0` comes first and is not negotiable.** `E0-S7` (person B denied at the database layer),
`E0-S8` (that denial watched going red), and `E0-S9` (the rule returning exactly `75810`) are the
three that make the rest trustworthy. `E6-S4` re-runs all three against the finished application —
because a gate that passed once on a skeleton proves nothing about what shipped.

## What is deliberately *not* in here

Anything the `03 PRD` marks out of scope, plus the five deferrals of `SRC-001 §14`. The expense
**update endpoint** appears (`P-REC-03`); its **screen** does not — that split is the client's own,
and the Bible reproduces it rather than quietly resolving it.

## Integrity, computed not claimed

```
55 rows          7 epics, 48 stories
195 acceptance criteria, every one binary
unresolved ParentID  : none
unresolved DependsOn : none
stories with no AC   : none
stories with no SourceRef : none
dependency cycles    : none
```

Re-run the generator rather than trusting this block.
