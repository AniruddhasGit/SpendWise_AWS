# SW-ADR-080 — PyJWT: pin the algorithm AND the version floor

| Field | Value |
|---|---|
| ADR | `SW-ADR-080` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-045` |
| Raised by | QA FINDING-15 (MEDIUM) — premise + a real gap |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-045` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-045` claimed an unpinned `jwt.decode` is a total authentication bypass. On PyJWT 2.x — which the rest of the stack forces — `algorithms` is a **required** argument and omitting it raises. The described bypass is real only on 1.x, which the ADR never mentioned and which nothing prevents being installed.

## Decision

**Keep `algorithms=['HS256']` pinned explicitly on every decode — it costs nothing and is correct on any version. **Add `PyJWT>=2.4` to the pinned dependencies**, which is the control the original ADR should have identified and did not.**

## Consequences

- The `SecureString` half of `SW-ADR-045` is unaffected and is now actually in the prep queue as item 7.
- Open and unresolved: whether `SecureString` with the default `aws/ssm` key needs an explicit `kms:Decrypt` grant on the execution role. Flagged in prep-queue item 7 as unverified rather than asserted either way.

---

*A superseding record, not an edit. `SW-ADR-045` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
