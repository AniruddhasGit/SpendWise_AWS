# FINDING — seven shipped routes are absent from the API spec of record

| | |
|---|---|
| Found | 2026-08-21, while narrowing `E6-S5` under `SW-ADR-153` |
| Status | **RESOLVED 2026-08-21** — all seven added to `contract.json`; downstream artifacts regenerated |
| Class | a generated document derived from an input that is missing rows |

## What is missing

`docs/03 PRD/api/contract.json` is the **spec of record** for the API. The PRD's §6 route table,
its §6.1 worked payloads, `error_codes.md` and `expected_summary.json` are all *generated* from it.
Seven routes the application serves are not in it:

| Route | Authorised by |
|---|---|
| `PATCH /api/auth/me` | `SW-ADR-148` C |
| `POST /api/auth/password` | `SW-ADR-148` D |
| `POST /api/auth/deactivate` | `SW-ADR-148` |
| `DELETE /api/auth/me` | `SW-ADR-150`, `CR-001` |
| `GET /api/auth/export` | `SW-ADR-148` |
| `GET /api/admin/overview` | M4 |
| `GET /api/admin/users/{user_id}/spending` | `SW-ADR-151`, `CR-001` |

Every one is approved, released and working. **Nothing here is a code defect.** The specification
simply never learned about capabilities that were added after it was written — the same root cause
as the `E6-S5` contradiction found the same day, and the same one behind
`SW-ADR-148`'s `included_in_bible = INCLUDED` cell being untrue.

Four routes appear in the contract and are *not* served — `POST /api/receipts/upload-url`,
`POST /api/receipts/attach`, `GET /api/receipts/{expense_id}/url`,
`DELETE /api/receipts/{expense_id}`. Those are correct: M5 is unbuilt, and a spec describing
work not yet done is a specification doing its job.

## Why it went unnoticed

`consistency_check.py` already had a `route-contract` check. It runs **one way**: it fails when a
*document* names a route the contract does not have. Nothing ran the other way — served route
absent from the contract — and that is the direction that rots, because it degrades every time
someone ships something rather than every time someone writes something.

The gap surfaced only by accident: `SW-ADR-153`'s new wording for `E6-S5` mentions
`DELETE /api/auth/me` by name, which tripped the one-way check, and the audit that followed found
the other six.

## The durable fix

A new **`route-coverage`** check in `tools/consistency_check.py` compares the routes the routers
actually declare against `contract.json`, and fails on any that are served but undocumented.

It reads the decorators **statically**, with `ast`, rather than importing the application.
Importing would need a valid configuration, and a check that cannot run on a bare clone is a check
that quietly stops running — which is the failure mode this whole finding is an instance of.

It also fails when it extracts **zero** routes, because an empty comparison passes for the wrong
reason. That guard is the same one that caught two vacuous tests in
`tests/test_capabilities_absent.py` on the same day: *a check that proves an absence must also
prove it looked.*

## Note on the red-proof

Until the seven routes are added, the selftest reports `route-coverage` as not firing — correctly.
The check emits one aggregate failure, so planting an eighth missing route cannot raise the count
above the one the real gap already produces. **The red-proof becomes meaningful the moment the
baseline is clean**, and it is re-run then rather than being declared green early.

## Resolved

All seven entries are in `contract.json`, derived from the code rather than described from memory:
handler decorators for method/path/models, and every `ApiError` reachable from each handler for
the error codes. Four model definitions had to be added with them — `ProfileUpdate`,
`PasswordChange`, `AdminOverview`, `AdminUserSpending` — because `contract-refs` fails any route
naming a model the contract does not define.

`generate_api.py` regenerated `SpendWise_PRD.md`, `error_codes.md` and `expected_summary.json`.
The §6 count sentence updated itself from 28 routes to 35 — it is computed, not typed. **The
day-one gate still asserts `daily_average_paise = 75810` through the regeneration.**

`consistency_check` PASS, and the selftest is now **18/18**: with the baseline clean,
`route-coverage` fires on a planted violation, which it could not do while seven real ones already
had it red.

## Two gaps this did NOT close

Recorded rather than filled, because both are `OPEN` and filling them would be inventing.

**1. None of the seven has a `P-xxx` spec id.** Every one of the original 28 entries cites one;
these seven carry `spec: []`. They were approved by ADR *after* the PRD's spec ids were assigned,
and no Bible story cites them either — the same gap `SW-ADR-153` recorded from the other end. Each
route's `note` says so in place of an invented id.

**2. `GET /api/admin/overview` has no authorising ADR.** It arrived with M4 in commit `8e75a4c`
and no record names it. `CR-001_CONTRACT.md §5.2` only amended its deactivated/deleted split, and
`SW-ADR-129` governs the `admin_expense_stats` function it depends on, not the route. Recorded as
**not determinable** rather than attributed to a record that does not say it.

Both want the same thing to close properly: Bible stories for the capabilities shipped after
`GOAL_07`, which is a scope decision and the client's to ask for.
