# SW-ADR-089 — Which calendar the application runs on

| Field | Value |
|---|---|
| ADR | `SW-ADR-089` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | AUTHORITY_RETURNED_TO_CLIENT |
| Supersedes | `SW-ADR-025` |
| Raised by | QA FINDING-2 (CRITICAL) — authority |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-025` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-025` ruled the application timezone as Asia/Kolkata — and stated **in its own consequences** that the choice is IRREVERSIBLE on the write path, because the submission instant is never stored, so rows misfiled across a day boundary can never be identified afterwards. `SW-ADR-015` says plainly that no delegation reaches an irreversible matter: it "still stops and waits". The one record that recognised the floor applied is the record that crossed it.

## Decision

**The ruling is **withdrawn**. The question returns to the client as `OPEN-TZ-01`, with Asia/Kolkata carried forward as the recommendation and the reasoning intact.**

## Consequences

- Downstream work is not blocked: `SW-ADR-053` and the 75,810 acceptance value proceed with the timezone marked `PROVISIONAL` under Art III.5's status law.
- The technical analysis in `SW-ADR-025` was sound and is not in dispute. What was wrong was who decided it.
- `SW-ADR-025`'s claim to have closed `OPEN-TZ-01` was also a dangling reference — that row did not exist until this remediation created it. Two defects, one root cause: a ruling that reached past its authority and then cited a register entry to look adjudicated.

---

*This record does not decide the question. It withdraws a decision the build session was not
entitled to make and returns it to the client. Art III.2: reversal happens by a new record,
never by editing the old one.*
