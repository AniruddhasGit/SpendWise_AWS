# Journey — the Person

| Field | Value |
|---|---|
| Persona | **Person** (`user`) — records what they spend, wants to understand where it went |
| Derived from | `02 BRD` §3 · `03 PRD` §4 E1–E4, §5 · `05 B DesignSystem` |
| Purpose | **Find what a per-screen specification misses: the seams between screens.** |

> Every step cites the `P-` row that specifies it. **A step with no citation is a defect in the
> PRD, not a gap in this document** — it is filed, never filled in here.

---

## J-U-01 — The first visit ever

| # | Intent | Surface | What happens | Spec |
|---|---|---|---|---|
| 1 | "I want to start tracking what I spend." | `/signin` | Lands on sign-in; switches to *create account*. | `P-ACC-01` |
| 2 | Enters email, password, display name. | `/signin` | Password under 12 characters → **inline 422 beneath the field**, not a toast. | `P-ACC-01`, §5.1 |
| 3 | Corrects and submits. | → `/` | Account created, **eight categories seeded**, signed in, dashboard. | `P-ACC-01`, `P-REC-05` |
| 4 | Sees the dashboard. | `/` | **First-run state**: no ribbon, no bars, one line of copy, one primary "Add your first expense". | `P-UND-06`, §5.2 |

**Seam checked:** step 4 is the *first screen any person ever sees* and it is not the same as
"your filter matched nothing". The PRD specifies both separately. ✅

## J-U-02 — Logging the first expense

| # | Intent | Surface | What happens | Spec |
|---|---|---|---|---|
| 1 | "₹340.50 on groceries today." | `/` | Opens the panel — from the right on desktop, up from the bottom on a phone. Focus is trapped; Escape closes. | §5.2 |
| 2 | Types the amount. | panel | Input restricted to two decimals, so the server's 422 is a backstop never met. | `P-REC-01`, `P-UND-07` |
| 3 | Picks the date. | panel | Defaults to today **in the browser** — the server never defaults it. | `P-REC-01`, `P-UND-03` |
| 4 | Picks Groceries. | panel | From their own eight. | `P-REC-05` |
| 5 | Submits. | panel | **Waits for confirmation. No optimistic insertion.** Then the summary refetches and the panel closes. | `P-REC-01`, §5.2 |
| 6 | Sees it. | `/` | Ribbon appears — one band at 100%. Total ₹340.50. Average = total ÷ days elapsed. | `P-UND-01`, `P-UND-02` |

**Seam checked:** step 5. The daily-average rule has exactly **one** implementation — server-side.
Optimistic insertion would have required a second one in the browser, and the day-one gate cannot
see a drift between two. ✅

## J-U-03 — A normal week

Six entries across four days, two uncategorised. Each is `P-REC-01`. On the dashboard:
the ribbon shows real proportions; **"Uncategorised" appears as a real band, last, in
`#948c87`**; the breakdown **sums exactly to the headline total** — an invariant asserted in
tests, not hoped for. `P-UND-05`

**Seam checked:** two entries with no category are guaranteed by `P-REC-05` (deleting a category
nulls the link). If the breakdown dropped them, the split would sum to less than the total
printed directly above it, in an app whose whole job is adding up. ✅

## J-U-04 — Reading the dashboard, changing the period

| # | Intent | What happens | Spec |
|---|---|---|---|
| 1 | "What did I spend this month?" | Chip → browser resolves it to explicit `from`/`to` **in Asia/Kolkata**; the server never guesses "this month". | `P-UND-03` |
| 2 | "And last month?" | Whole previous calendar month. Reads the same today as it will next week — a closed period does not drift. | `P-UND-03`, `P-UND-02` |
| 3 | Refreshes the page. | **The period survives** — it lives in the query string. | §3.2 |
| 4 | Presses back. | Returns to the previous period, not out of the app. | §3.2 |

**Seam checked:** steps 3–4. Without the period in the URL, a refresh silently resets it and the
person concludes their data changed. ✅

## J-U-05 — Filtering from the ribbon

| # | Intent | What happens | Spec |
|---|---|---|---|
| 1 | Clicks the Groceries band. | **Total, count, average, day bars and the list all re-scope.** | `SW-ADR-109`, §5.2 |
| 2 | Looks at the ribbon. | **It does not re-scope** — it stays whole-period so proportions stay visible and other bands stay reachable. Groceries is emphasised; the rest dim. | §5.2 |
| 3 | Uses the keyboard instead. | One Tab reaches the ribbon; `←`/`→` move between bands; Enter toggles; Escape clears. Each band announces "Groceries: ₹2,140.00, 34% of total". | design system §5.1 |
| 4 | Clicks the active band again. | Filter clears. | §5.2 |

**Seam checked:** step 1. If the headline did not follow, the page would show a total visibly
disagreeing with the per-day subtotals printed beneath it. ✅
**Seam checked:** step 3. The ribbon is the *primary filter control* — mouse-only would have made
the app's main interaction unreachable by keyboard. ✅

## J-U-06 — Attaching a receipt

| # | Intent | What happens | Spec |
|---|---|---|---|
| 1 | Has a photo of the bill. | Client checks type and size **first**, so a 10 MB file is not uploaded before being refused. | `P-RCP-01` |
| 2 | Uploads. | Straight to storage via a presigned POST whose policy asserts size and type — the file never passes through the container. | `P-RCP-01` |
| 3 | Closes the tab mid-upload. | The staged object **expires after one day**. No orphan lives forever. | `P-RCP-01` |
| 4 | Views it later. | A five-minute signed link, resolved from their own expense record — the key is never accepted from the browser. | `P-RCP-02` |
| 5 | Storage unconfigured. | The control is **hidden**, not broken — `receipts_enabled` says so. | `P-RCP-03` |

**Seam checked:** step 3 — abandonment between the three steps. **Step 5 is the client's own
default local experience**, so it is the state they will personally see most often. ✅

## J-U-07 — Coming back after a month away

Signs in — within the 14-day idle window? No: **the session has expired.** Signs in again
(`P-ACC-04`). The dashboard opens on "this month", which is empty, so they see the
**"nothing in this period"** state — *not* the first-run state, which would wrongly suggest the
account was reset. `P-UND-06`

**Seam checked:** two different empty states, one screen. The PRD distinguishes them. ✅

## J-U-08 — Locked out

| # | Intent | What happens | Spec |
|---|---|---|---|
| 1 | Forgets the password. | Sign-in fails with a **generic 401** — unknown email, wrong password and deactivated account are indistinguishable. | `P-ACC-03` |
| 2 | Tries repeatedly. | Rate limited at 10/min. **429 shows a countdown** and disables submit — otherwise they retry and extend the block. | `P-ACC-03`, §5.1 |
| 3 | Contacts the administrator. | Out of band — there is no self-service reset, by ruling. | `P-ADM-04` |
| 4 | Receives a code. | Handed over out of band; the administrator saw it once. | `P-ADM-04` |
| 5 | Redeems it. | **Third mode on the sign-in page** — where a signed-out person already is. | `P-ACC-07` |
| 6 | Mistypes it. | "This reset code is not recognised." — distinct from *used* and from *expired*. | `P-ACC-07` |
| 7 | Gets it right. | Password replaced, **every old session revoked in the same transaction**, returned to sign-in. No auto-login. | `P-ACC-07` |

**Seam checked:** step 5 is the one this journey exists to find. `SRC-001` retained the
completion endpoint and listed no screen for it — built literally, the locked-out person, the
exact persona the administrator role exists for, would have received a code and a dead end.
Closed by `SW-ADR-110`. ✅

## J-U-09 — Signed out from under them

Mid-entry, an administrator revokes their sessions. The next request returns 401. **One
interceptor** clears state, routes to sign-in with a reason banner, and **suppresses duplicate
redirects** — the dashboard fires more than one request, so a per-call handler would redirect
twice. The half-typed expense is held in memory. `§5.4`

**Seam checked:** the dashboard's multi-request load against a single-redirect requirement. ✅

---

## Defects filed against the PRD from this journey

**None.** Every step resolved to a specification.

**That is a suspicious result and it is stated as one.** This journey was walked *after* the
`GOAL_02` sweep had already found 127 undetermined decisions and Fable 5 had ruled all 38 open
rows — so the seams these journeys exist to expose were largely closed before the walk began.
The honest reading is that this document **confirms** rather than **discovers**, and its value
here is the coverage evidence below, not a finding count.

**Where a fresh reader should look hardest**, because this walk could not: the 400-day range cap
and its error message were never exercised; no step drove two browser tabs at once; and nothing
here tested what a person sees when the *server* is down rather than their session expired.

## Coverage

| Surface (PRD §3.2) | Reached by |
|---|---|
| `/signin` — sign in | J-U-08 |
| `/signin` — create account | J-U-01 |
| `/signin` — redeem code | J-U-08 |
| `/` dashboard | J-U-02…07, J-U-09 |
| not-found | *not reached* — see above |
| `/admin`, `/admin/audit` | administrator journey |

**Person-facing `P-` rows traversed:** `P-ACC-01`, `03`, `04`, `05`, `06`, `07` · `P-REC-01`,
`04`, `05` · `P-UND-01`…`07` · `P-RCP-01`, `02`, `03`.
**Not traversed:** `P-REC-02` (list filters directly), `P-REC-03` (update — the endpoint exists,
the screen does not, per `SRC-001 §14`).
