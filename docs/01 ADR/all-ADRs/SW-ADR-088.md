# SW-ADR-088 — AWS claims in build-session ADRs are labelled reasoned, not observed

| Field | Value |
|---|---|
| ADR | `SW-ADR-088` |
| Pack | `SPENDWISE_V1` |
| Type | ANNOTATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — (annotation; corrected by `SW-ADR-132`) |
| Raised by | QA FINDING-19 (MEDIUM) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-023` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

Art VIII.3 requires every claim the build session makes about AWS behaviour to be labelled reasoned rather than observed. The two client-decided ADRs (`SW-ADR-008`, `SW-ADR-014`) carry explicit unverified lines. **Not one of the 48 build-session ADRs does**, including those reasoning from an instance class the client has not yet created.

## Decision

**Every AWS-touching claim in `SW-ADR-023`, `047`, `065`, `068`, `069` and `070` is `UNVERIFIED — reasoned, not observed`. `SW-ADR-065`'s connection arithmetic is explicitly conditional on the instance class the client reports back under prep-queue item 2.**

## Consequences

- The ~110-connection figure follows RDS's documented `DBInstanceClassMemory/9531392` formula on 1 GiB. The formula is documented; the instance is hypothetical.
- A labelling discipline that lapses silently across a 48-record pass is exactly what Art VIII.3 exists to prevent, and it lapsed.

---

*An annotation, not a supersession. The six records named above keep their decisions in full;
only their AWS-touching claims gain a label. `SW-ADR-132` corrects the `Supersedes` field that
had wrongly withdrawn `SW-ADR-023`.*
