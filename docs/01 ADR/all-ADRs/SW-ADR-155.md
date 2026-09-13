# SW-ADR-155 — The build session builds AWS and the pipeline, superseding SW-ADR-005

| Field | Value |
|---|---|
| ADR | `SW-ADR-155` |
| Pack | `SPENDWISE_V1` |
| Type | DELIVERY_MODEL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-09-13 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Supersedes | `SW-ADR-005` |
| Sources | Client instruction, 2026-09-12 and 2026-09-13 |

## Context

`SW-ADR-005` held that the build session writes application code only: no pipeline files, no
infrastructure code, nothing created in AWS. The client intended to build DEV, UAT and PROD by hand
in order to practise the DevOps role, and that reason was sound.

It stopped being the situation. Across 2026-09-12 and 2026-09-13 the client directed the build
session to deploy to AWS, then to build the three environments and the pipeline, in successively
more explicit terms — *"build it"*, *"continue the infra build"*, *"start building the infra, we do
not have time"*, and finally a scope confirmation of *"Everything: branches, GitHub, AWS, CD"*.

By the time this record was written the session had already created an OIDC identity provider, six
IAM roles, two ECS services, SSM parameters, log groups, security-group rules and a CD pipeline.
`CLAUDE.md` still instructed every future session that none of that was permitted. A rule that the
repository contradicts on disk is worse than no rule: the next session has to guess which of the
two is stale, and guessing is what this project's whole method exists to prevent.

## Options considered

- **A.** Leave `SW-ADR-005` standing and treat the AWS work as an undocumented exception.
- **B.** Edit `SW-ADR-005` to match what happened.
- **C.** Supersede it with a new record that says what changed, when, and on whose authority.

## Decision

**C.** `SW-ADR-005` is SUPERSEDED. The build session may create AWS resources and pipeline files.

Option B is not available: accepted decisions are immutable in this method, and rewriting one to
match events destroys the only record that the decision was ever different. Option A is how a
document set stops being trustworthy.

## Consequences

- **The RISK clause in `SW-ADR-005` is discharged, not inherited.** That record warned the build
  session would never observe the app running in AWS, so every AWS claim would be *reasoned, not
  observed*. That is no longer true, and claims must now be labelled the other way: the session
  observes AWS directly, and an unobserved claim is a defect rather than an expected limitation.

- **The client's original purpose is not abandoned.** Everything created is committed under
  `infra/` as scripts and policy documents, with the reasoning in comments. Practising DevOps by
  reading and re-running a documented pipeline is a different exercise from building it by hand,
  and a poorer one in some ways; it is a fair trade only because it was made deliberately and under
  time pressure the client named.

- **The honesty floor is unchanged.** `CONSTITUTION.md` Art VII still governs. Infrastructure
  evidence is held to the same standard as code evidence: *here is the command and here is the
  output*, never *the pipeline went green*.

- **`CLAUDE.md` must be updated** in the same commit as this record, or the contradiction this ADR
  exists to remove survives in the file every session actually reads.

- **What remains outside this record:** billing decisions, and anything that changes what the
  product is. `Reserved` in `CLAUDE.md` is untouched. Opening a database port to the public
  internet is reserved regardless of convenience — it was declined during this session and referred
  to the client.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file.*
