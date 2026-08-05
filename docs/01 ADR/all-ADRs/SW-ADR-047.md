# SW-ADR-047 — Uploads use a presigned POST with a signed content-length and type policy

| Field | Value |
|---|---|
| ADR | `SW-ADR-047` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §8.1` · `SRC-001 §8.3` · `SW-ADR-014` |

## Context

SRC-001 §8.3 states a 10 MB cap and a JPG/PNG/WEBP/PDF allowlist as facts. A plain presigned PUT enforces NEITHER — it is a bearer capability to write anything of any size, and the server that signed it never sees the bytes. An object stored with Content-Type text/html is later served as HTML from a signed URL: stored cross-site scripting on an AWS origin.

## Options considered

- A. Presigned POST with a policy asserting content-length-range and an allowed Content-Type, plus Content-Disposition: attachment on the object.
- B. Signed PUT with ContentType and ContentLength.
- C. Validate after the fact on attach.

## Decision

**A.**

## Consequences

- This makes SRC-001 §8.3's stated constraints true rather than aspirational.
- The size hole is also a direct cost-abuse vector on an account whose entire posture is 'nothing paid' (SW-ADR-014).
- S3 CORS is required for this and SRC-001 §2.4's 'no CORS to configure' is wrong — see SW-ADR-069.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
