# SW-ADR-045 — JWT algorithm is pinned; both secrets are SSM SecureString

> **⚠ AMENDED 2026-08-05 by `SW-ADR-080` (QA FINDING-15 (MEDIUM) — premise + a real gap).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-045` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §2.1` · `SRC-001 §11.4` · `SW-ADR-014` |

## Context

PyJWT's decode accepts whatever algorithm the token's own header claims unless `algorithms` is passed explicitly — the alg:none and HS/RS confusion class, which is a total authentication bypass rather than a degradation. Separately, the client creates SSM parameters by hand from a queue that never says SecureString, and a plain String parameter is unencrypted and needs no KMS grant, so the least-effort choice is the insecure one.

## Options considered

- A. HS256 with algorithms=['HS256'] pinned on every decode; DATABASE_URL and JWT_SECRET both SecureString.
- B. Leave the defaults.

## Decision

**A.**

## Consequences

- An unpinned decode is an authentication bypass, not a weakness.
- SecureString must be added to the AWS prep queue — the client is building this by hand and the queue is the only channel that reaches them before the parameter exists.
- Rotating JWT_SECRET signs everyone out instantly with no overlap window. Recorded as OPEN-ROTATE-01.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
