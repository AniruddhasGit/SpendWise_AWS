# SW-ADR-069 — S3 requires a CORS rule — SRC-001 §2.4's 'no CORS' premise is wrong

| Field | Value |
|---|---|
| ADR | `SW-ADR-069` |
| Pack | `SPENDWISE_V1` |
| Type | OPERATIONS |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §2.4` · `SRC-001 §8.1` · `SW-ADR-005` |

## Context

SRC-001 §2.4 states there is no CORS to configure because the browser only ever talks to one origin. That is true for the API and FALSE for §8.1's direct-to-S3 upload, where the browser talks to a second origin. Without a bucket CORS policy, every receipt upload fails with an opaque console error and no usable response body, so the SPA cannot even report why.

## Options considered

- A. File an erratum against §2.4 and add the bucket CORS rule to the AWS prep queue as a client action.
- B. Proxy uploads through the container.
- C. Discover it at first upload.

## Decision

**A.**

## Consequences

- B would kill §8.1's entire rationale — large uploads would occupy an ECS task and hit request-size limits.
- This is the clearest instance of the SW-ADR-005 risk: a claim about AWS behaviour that is reasoned rather than observed, and here the reasoning is simply wrong.
- Filed as ERRATUM E-8 against SRC-001.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
