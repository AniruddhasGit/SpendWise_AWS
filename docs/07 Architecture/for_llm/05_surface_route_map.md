# Surfaces and routes

| Route | Guard | Spec |
|---|---|---|
| `/signin` | anonymous | `P-ACC-01`, `P-ACC-03`, `P-ACC-07` |
| `/` | signed in | `P-UND-01`…`P-UND-07` |
| `/admin` | `require_admin` | `P-ADM-01`…`P-ADM-09` |
| `/admin/audit` | `require_admin` | `P-ADM-08` |
| *(unmatched)* | any | not-found screen |

| API | Guard |
|---|---|
| `POST /api/auth/register · login · reset/complete` | anonymous, rate limited |
| `POST /api/auth/logout` · `GET /api/auth/me` | signed in |
| `GET·POST /api/categories` · `PATCH·DELETE /api/categories/{id}` | owner, RLS |
| `GET·POST /api/expenses` · `PATCH·DELETE /api/expenses/{id}` | owner, RLS |
| `GET /api/expenses/summary` | owner, RLS |
| `/api/receipts/*` | **owner only — no administrative path exists** |
| `/api/admin/*` | `require_admin` as a **router** dependency, applied once |
| `/healthz` · `/readyz` | anonymous, bodiless |

**`require_admin` is declared once**, on the router, never per handler — `SRC-001 §4.3`'s stated
reason: *"because I will forget one."*

**Not-yours and not-found are the same response: 404, on every verb** (`SW-ADR-050`). A 403 on an
existing record is an id oracle. This is also what makes sequential integer ids safe — the two
decisions must be reversed together or not at all.

---

## On granularity, so a two-way check does not misread it

This map groups where the PRD enumerates: `/api/admin/*` here is nine endpoints in
`03 PRD` §6, and `/api/receipts/*` is four. That is deliberate — **this document orients a
session; the PRD is the contract.**

A naive set-difference between the two therefore reports a mismatch that is not one. The
correct check is *containment*: every PRD route must resolve to an entry here, by exact match
or by a wildcard prefix. Verified 2026-08-05 — **all 18 PRD routes resolve, none missing.**
