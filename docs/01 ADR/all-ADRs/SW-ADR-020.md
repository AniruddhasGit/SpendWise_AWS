# SW-ADR-020 — One container serves both the API and the built frontend

| Field | Value |
|---|---|
| ADR | `SW-ADR-020` |
| Pack | `SPENDWISE_V1` |
| Type | ARCHITECTURE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S2.4` · `SRC-001 S9.5` |

## Context

SRC-001 S2.4 rules out a separate CloudFront distribution for the frontend in favour of a single origin.

## Options considered

- A. One image serving both, mounted via StaticFiles with a catch-all returning index.html.
- B. Separate frontend distribution - explicitly refused by the client.

## Decision

**A. One image, one repo, one service, one deploy.**

## Consequences

- No CORS to configure, because the browser only ever talks to one origin.
- Client-side routing works because a catch-all route returns index.html for unmatched paths.
- Vite's dev server proxies /api to port 8000 so the session cookie behaves identically locally and when deployed (SRC-001 S9.5).
- The three fonts of SRC-001 S9.4 are self-hosted rather than fetched from Google Fonts - the same single-origin reasoning that rejected a CDN applies to them.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
