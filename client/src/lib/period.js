/**
 * Periods, in Asia/Kolkata, expressed as calendar dates.
 *
 * E3-S2 AC1: "This month" is the first and last day of the current month **in
 * Asia/Kolkata** — not in the browser's zone. A person in London opening this
 * at 20:00 on the 31st is already on the 1st in Kolkata, and `new Date()`
 * would put them in the wrong month. `SW-ADR-035` fixes the business day to
 * Asia/Kolkata for exactly this reason; the client honours the same rule.
 *
 * Every value here is a `YYYY-MM-DD` STRING. No `Date` object crosses this
 * module's boundary, because a `Date` is an instant and a spending day is not.
 */

const ZONE = 'Asia/Kolkata'

/**
 * Today in Asia/Kolkata as `YYYY-MM-DD`.
 *
 * `en-CA` is the shortest route to ISO order from `Intl` — it formats as
 * `2026-08-05` natively, so there is no re-assembly step to get wrong.
 */
export function today(now = new Date()) {
  const override = window.__SPENDWISE_TODAY__
  // A Playwright hook, and only that. `SW-ADR-039` freezes the day-one gate to
  // 2026-08-05, so the browser test that reads 758.10 off the screen needs the
  // client to agree with `APP_TODAY_OVERRIDE`. It is read from `window`, set by
  // an init script, and never from a URL parameter — a URL parameter would let
  // anyone shift their own "today" and, with it, `days_elapsed`.
  if (override) return override
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(now)
}

const pad = (n) => String(n).padStart(2, '0')

/** Arithmetic on the PARTS, never on a Date — no zone, so no shift. */
function daysInMonth(year, month) {
  return [31, isLeap(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
}

function isLeap(y) {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0
}

export function addDays(iso, delta) {
  let [y, m, d] = iso.split('-').map(Number)
  d += delta
  while (d < 1) {
    m -= 1
    if (m < 1) { m = 12; y -= 1 }
    d += daysInMonth(y, m)
  }
  while (d > daysInMonth(y, m)) {
    d -= daysInMonth(y, m)
    m += 1
    if (m > 12) { m = 1; y += 1 }
  }
  return `${y}-${pad(m)}-${pad(d)}`
}

export function monthOf(iso) {
  const [y, m] = iso.split('-').map(Number)
  return { from: `${y}-${pad(m)}-01`, to: `${y}-${pad(m)}-${pad(daysInMonth(y, m))}` }
}

export function previousMonthOf(iso) {
  let [y, m] = iso.split('-').map(Number)
  m -= 1
  if (m < 1) { m = 12; y -= 1 }
  return { from: `${y}-${pad(m)}-01`, to: `${y}-${pad(m)}-${pad(daysInMonth(y, m))}` }
}

/**
 * The named periods, in the order they appear in the picker.
 *
 * `SRC-001 §9.1` names this month, last month and last 30 days. "Custom" is
 * what the URL falls back to when someone edits `?from=`/`?to=` by hand or
 * lands on a shared link — it is a STATE, not a fifth chip, because a chip
 * would imply a picker that does not exist yet.
 */
export const PERIODS = [
  { id: 'this-month', label: 'This month', range: (t) => monthOf(t) },
  { id: 'last-month', label: 'Last month', range: (t) => previousMonthOf(t) },
  { id: 'last-30', label: 'Last 30 days', range: (t) => ({ from: addDays(t, -29), to: t }) },
]

/** Which named period a range corresponds to, or `null` for a custom one. */
export function identify(range, t = today()) {
  for (const p of PERIODS) {
    const r = p.range(t)
    if (r.from === range.from && r.to === range.to) return p.id
  }
  return null
}

export function labelFor(range, t = today()) {
  const id = identify(range, t)
  const named = PERIODS.find((p) => p.id === id)
  return named ? named.label : 'Custom range'
}

// ── URL state ──────────────────────────────────────────────────────────────
// E3-S2 AC2 and AC3: the period lives in the QUERY STRING, so reloading keeps
// it and Back returns to the previous period rather than leaving the app. That
// second one is why this uses pushState and a `popstate` listener rather than
// component state — component state gives a Back button that exits to whatever
// page came before SpendWise, which is the bug the criterion names.

const ISO = /^\d{4}-\d{2}-\d{2}$/

export function readRange(search = window.location.search) {
  const p = new URLSearchParams(search)
  const from = p.get('from')
  const to = p.get('to')
  // A malformed or reversed range in a hand-edited URL falls back to the
  // default rather than being sent to the server to be refused. The server
  // still refuses it if it ever arrives — this is not the guard, it is the
  // courtesy.
  if (ISO.test(from || '') && ISO.test(to || '') && from <= to) return { from, to }
  return monthOf(today())
}

export function readCategory(search = window.location.search) {
  const raw = new URLSearchParams(search).get('category')
  if (raw === 'none') return 'none'
  const n = Number(raw)
  return Number.isInteger(n) && n > 0 ? n : null
}

export function writeState({ from, to, category }, { replace = false } = {}) {
  const p = new URLSearchParams()
  p.set('from', from)
  p.set('to', to)
  if (category === 'none') p.set('category', 'none')
  else if (category) p.set('category', String(category))
  const url = `${window.location.pathname}?${p.toString()}`
  if (replace) window.history.replaceState(null, '', url)
  else window.history.pushState(null, '', url)
}
