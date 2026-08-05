# Journey index

| Journey | Persona | Surfaces | Seam it crosses |
|---|---|---|---|
| `J-U-01` first visit | person | `/signin` → `/` | registration → seeded categories → first-run dashboard |
| `J-U-02` first expense | person | `/` + panel | panel → server → summary refetch |
| `J-U-03` a normal week | person | `/` | expenses → breakdown → the sum-equals-total invariant |
| `J-U-04` changing period | person | `/` | chip → URL → refresh → back button |
| `J-U-05` filtering | person | `/` | ribbon → every other number on the page; pointer → keyboard |
| `J-U-06` receipts | person | `/` + panel | browser → storage → server, abandonable at each step |
| `J-U-07` a month away | person | `/signin` → `/` | expiry → sign-in → *which* empty state |
| `J-U-08` locked out | person | `/signin` | failure → rate limit → administrator → out of band → redemption |
| `J-U-09` signed out mid-use | person | `/` → `/signin` | revocation → multi-request 401 → single redirect |
| `J-A-01` bootstrap | admin | startup | empty database → claim → refuse-to-start |
| `J-A-02` cannot get in | admin | `/admin` | search → reset → code shown once → audit row |
| `J-A-03` ending a session | admin | `/admin` | revoke → the other person's next request |
| `J-A-04` a leaver | admin | `/admin` | deactivate → three enforcement points |
| `J-A-05` second administrator | admin | `/admin` | promote/demote → sessions; the last-admin guard; peer reset |
| `J-A-06` after an incident | admin | `/admin/audit` | action → record → read-audit recursion |
| `J-A-07` what is refused | admin | `/admin` | every "no" in the permission matrix |

## What these journeys are for

A per-screen specification says what each screen does. It cannot say what happens **between**
screens — and that is where specifications are thin. Each journey names the seams it crossed, and
every step cites the `P-` row that specifies it. **A step with no citation is a defect in the PRD,
not a gap here.**

## Honest result

**Zero defects filed.** Both journey documents state plainly that this is a **suspicious** result
rather than a good one, and both name what they could not reach: the 400-day range cap, concurrent
browser tabs, a server-down state (as distinct from an expired session), two administrators acting
on one account, and audit pagination at volume.

The reason is chronological. These walks ran **after** `GOAL_02` swept 127 undetermined decisions
and Fable 5 ruled all 38 open rows — the seams had already been closed by the two passes designed
to close them.

Had journeys run *before* that sweep, these are exactly the two defects they would have found:

- **`SW-ADR-110`** — the reset code with no screen to type it on. `SRC-001` kept the completion
  endpoint and listed no page for it, so the locked-out person — the exact persona the
  administrator role exists for — would have received a code and a dead end.
- **`SW-ADR-098`** — the last-administrator guard covered demotion but not deactivation, so the
  identical unrecoverable state was reachable by a different button.

Both are seam defects: neither is visible while reading any single screen's specification.

## Surface coverage

| Surface (PRD §3.2) | Reached by |
|---|---|
| `/signin` — sign in | `J-U-08` |
| `/signin` — create account | `J-U-01` |
| `/signin` — redeem code | `J-U-08` |
| `/` dashboard | `J-U-02`…`J-U-07`, `J-U-09` |
| `/admin` | `J-A-02`…`J-A-05`, `J-A-07` |
| `/admin/audit` | `J-A-06` |
| not-found / no-access | **not reached** — recorded, not hidden |
