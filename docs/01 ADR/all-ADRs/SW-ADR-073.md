# SW-ADR-073 — Build and schema version live on `/readyz` behind a flag

| Field | Value |
|---|---|
| ADR | `SW-ADR-073` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-070` |
| Raised by | QA FINDING-6 (HIGH) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-070` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-064` puts build and schema version on `/readyz`. `SW-ADR-070` makes `/readyz` bodiless and puts version behind `require_admin`. Both APPROVED, directly contradictory, and Art II.1 cannot separate two same-rank records. Worse, `SW-ADR-005` — a **client** decision — requires "a health endpoint reporting build and schema version", so a build-session ruling had overridden a client one.

## Decision

**`/healthz` stays bodiless (200/503). `/readyz` returns `{status, revision, build}` when `EXPOSE_VERSION` is set, and `{status}` alone when it is not. Default is **on**, because `SW-ADR-005`'s obligation is a client decision and the build session may not quietly discharge it.**

## Consequences

- `SW-ADR-064`'s stated purpose survives: 'which image is running right now' is the first question of every incident, on a deployment with no load balancer and no monitor.
- `SW-ADR-070`'s concern also survives: the client can turn disclosure off with one variable.
- The client may reverse the default. That is a disclosure posture, and it is theirs.

---

*A superseding record, not an edit. `SW-ADR-070` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
