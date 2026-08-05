# SW-ADR-032 — Reset tokens: SHA-256, unique, one live token per user

| Field | Value |
|---|---|
| ADR | `SW-ADR-032` |
| Pack | `SPENDWISE_V1` |
| Type | SECURITY |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.7` · `SW-ADR-012` |

## Context

SRC-001 §10.7 requires tokens hashed, single use, one-hour expiry, but names no algorithm and does not say how many unexpired tokens may coexist for one user.

## Options considered

- A. SHA-256 of a 32-byte urandom token; token_hash CHAR(64) UNIQUE; issuing a new token invalidates every outstanding one for that user in the same transaction.
- B. bcrypt the token.
- C. Allow multiple live tokens.

## Decision

**A.**

## Consequences

- bcrypt is unnecessary here — the token is high-entropy random, not a human-chosen password, so a fast hash is correct and a slow one only adds latency to a path that is already rate-limited.
- C was rejected: multiple live tokens means an admin who reissues cannot tell the user which code is valid, and every old code stays usable for its remaining hour.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
