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
| `GET·POST /api/expenses` · `GET·PATCH·DELETE /api/expenses/{expense_id}` | owner, RLS |
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

This map groups where the PRD enumerates: `/api/admin/*` here is **seven** endpoints in (nine is the count of `P-ADM-*`
specifications, a different set, and `P-ADM-09` specifies an endpoint that deliberately does
not exist)
`03 PRD` §6, and `/api/receipts/*` is four. That is deliberate — **this document orients a
session; the PRD is the contract.**

A naive set-difference between the two therefore reports a mismatch that is not one. The
correct check is *containment*: every PRD route must resolve to an entry here, by exact match
or by a wildcard prefix.

**Verified 2026-08-05: the route inventory is generated from `docs/03 PRD/api/contract.json` (`SW-ADR-140`), and `consistency_check.py` fails if any route a test names is missing from it. This note previously claimed 25 routes verified while the set omitted `GET /api/expenses/{expense_id}`, which a SEV-1 case requires.**

> **Correction, recorded rather than quietly fixed.** The first version of this note claimed
> "all 18 PRD routes resolve" — written *before* the check was re-run correctly, and the run it
> was written alongside had actually reported **10 routes uncovered**. Both numbers were wrong:
> there are 26 API routes (28 with `/healthz` and `/readyz`), generated from `contract.json`, and the 10 were an artefact of a regex that missed paths sharing a table
> cell (`POST /api/auth/register · login · reset/complete`). The map was never wrong; the
> measurement was, and then the claim was written ahead of the measurement.
>
> This is exactly the K1 failure the log deny-list and the citation checker exist to prevent, and
> it happened here in prose where neither could see it. Kept visible because a corrected claim
> with no record of the correction is how a document set stops being trustworthy.
