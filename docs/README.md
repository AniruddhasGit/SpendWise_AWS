# docs/ — the SpendWise delivery document set

Numbered in **dependency order**. Each folder is derived from the ones above it and **cites them**.
Nothing appears out of thin air: a statement without a source carries an `ASSUMED` flag and can
never become a `MUST`.

```
00 SourceOfTruth ──► 02 BRD ──► 03 PRD ──► 05 Bible ──► 06 DataModel ──► code
       │                                                      ▲
       └──► 01 ADR ───────────────────────────────────────────┘
            every ruling, and proof it landed in each document above
```

| # | Folder | What it is | State |
|---|---|---|---|
| 00 | **SourceOfTruth** | `SRC-001` — the client's requirements, verbatim, clause-numbered, **frozen and SHA-256 hashed**. Seven errata at its foot. Never edited. | **written** |
| 01 | **ADR** | 22 decision records + `ADR_DECISION_RELEASE_LEDGER.tsv`. Fail-closed. | **written** |
| 02 | **BRD** | Business requirements — what and why. No technology. | empty |
| 03 | **PRD** | Product requirements — every screen, rule and error. **The code is written from this.** | empty |
| 05 | **Bible** | Epics → stories → tasks, each with binary `AcceptanceCriteria`. | empty |
| 05 B | **DesignSystem** | Paper and pine green; Instrument Serif / Sans / IBM Plex Mono; tabular figures — as tokens. | empty |
| 06 | **DataModel** | A **package, not a document**: `datamodel.json`, `schema.sql`, `migrations/`, `security.sql` (RLS), `permissions.tsv`, `TRACEABILITY.tsv`, `AGENT_CONTRACT.md`. | empty |
| 07 | **Architecture** | `for_humans/` and `for_llm/`. | empty |
| 08 | **SIT** | Test cases as rows, each citing the Bible story it proves. | empty |
| 09 | **NegativeTesting** | Weighted hard at one thing: user B trying to see user A's money. | empty |
| 10 | **EngineeringLedger** | The build ledger — one row per unit of work, with `Milestone` and `Status`. **`/ss` reads this to report the frontier.** | empty |
| 11 | **Journeys** | User and admin persona journeys. | empty |
| 12 | **DesignReview** | The pre-code audit: fresh agents attack every document above before a line is written. | empty |
| 13 | **Fixes for Design Review** | What the audit found, and its repair. | empty |
| 14 | **Project_Plan** | Milestones and the cutover plan. | placeholder |
| 15 | **ChangeRequest** · 20 **UAT** · 30 **Deployment** · 35 **Hypercare** · 40 **AMS** | Lifecycle. `30 Deployment` already holds the client's AWS prep queue. | placeholders |

## The four rules that make this work

**1. Provenance on every line.** Every requirement downstream cites `SRC-001 §n` or an
`APPROVED` ADR. You can trace any sentence back to something the client actually said.

**2. Status law.** `RULED` (decided, cited) · `PROVISIONAL` (written, ruling outstanding) ·
`OPEN` (**escalate, never invent**) · `ASSUMED` (inference, never a constraint). An agent that hits
`OPEN` and fills in something plausible has committed the cardinal sin.

**3. Fail-closed decisions.** Every ADR starts `NOT_DECIDED` + `HOLD_PENDING_DECISION` +
`NOT_RELEASED`. **Silence never means approval.** Accepted decisions are immutable — a reversal is a
new superseding record, never an edit. `SW-ADR-004` is the worked example: superseded one hour
later, retained unedited and marked.

**4. Incorporation is tracked, not assumed.** The ledger's `included_in_brd` / `_prd` / `_bible` /
`_datamodel` columns prove a decision actually *landed* in each document rather than being decided
and forgotten. All 22 rows read `NOT_INCLUDED` today — correctly, since those documents do not yet
exist.

## Fingerprints

`00 SourceOfTruth/fingerprints.json` holds a SHA-256 per frozen source.
**If a hash changes, every artifact derived from it is invalid and must be re-derived** — never
silently reused.

## Where the open questions live

`CONSTITUTION.md` **Article X**. Nine are open. `OPEN-NAME-01` is the one that matters formally:
until a named human signs the ratification block, the Constitution is **UNADOPTED** and all 22 ADRs
carry a "recorded while ungoverned" caveat.

## Reading rules

- For **decision status**, trust the ledger. For **document versions**, trust the files on disk.
  For **paths**, trust the repo tree — never a path quoted in prose.
- Authority on conflict: raw `SRC-001` → a client ruling → an `APPROVED` ADR → PRD → BRD → Bible →
  everything else. **Stricter always wins.**
