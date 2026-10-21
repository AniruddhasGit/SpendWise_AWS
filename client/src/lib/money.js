/**
 * THE money formatter. There is exactly one, and this is it.
 *
 * `DESIGN-SYSTEM.md §3`: "One shared formatter; no component invents its own."
 * `scripts/lint-tokens.mjs` greps for `toLocaleString` and `Intl.NumberFormat`
 * anywhere else in `src/` and fails the build — because the failure mode is not
 * a wrong number, it is $1,234,567.89 on one screen and $1.234.567,89 on the
 * next, which reads as a bug in the arithmetic.
 *
 * Amounts are US dollars (`SW-ADR-157`). The integer field is still named
 * `*_paise` on the wire and in the database: it holds cents, 100 to the unit,
 * exactly as before, and renaming a contract field is not a display change.
 *
 * **The client never divides by 100.** The server sends integer paise and a
 * plain decimal string; splitting the integer with `%` and `/` on integers is
 * exact, and `paise / 100` is a float the moment the number gets large.
 */

// `en-US` groups by thousands: $1,234,567.89 (`SW-ADR-157`, which replaced
// `SW-ADR-056`'s rupees and lakh grouping). Constructed once — a formatter per render is measurably slow
// and there is nothing per-call about it.
const GROUPER = new Intl.NumberFormat('en-US', { useGrouping: true })

/**
 * 758100 -> "$7,581.00". Integer paise in, display string out.
 */
export function dollars(paise) {
  if (paise === null || paise === undefined) return null
  const negative = paise < 0
  const abs = Math.abs(paise)
  // Integer arithmetic throughout. `Math.trunc(abs / 100)` is exact for every
  // value below 2^53 paise, which is $90 trillion — comfortably past the
  // 10,000,000,000.00 ceiling the contract puts on a single amount.
  const whole = Math.trunc(abs / 100)
  const fraction = abs % 100
  const body = `$${GROUPER.format(whole)}.${String(fraction).padStart(2, '0')}`
  return negative ? `-${body}` : body
}

/**
 * The same value with no symbol, for an `<input>` or a title attribute.
 */
export function plain(paise) {
  if (paise === null || paise === undefined) return null
  const abs = Math.abs(paise)
  const sign = paise < 0 ? '-' : ''
  return `${sign}${Math.trunc(abs / 100)}.${String(abs % 100).padStart(2, '0')}`
}

/**
 * A whole-number percentage, already computed by the server. Here so that the
 * `%` sign is written once and a component never assembles one by hand.
 */
export function percent(n) {
  return `${n}%`
}

/**
 * "5 days" / "1 day". Small, but it is the kind of string that otherwise gets
 * written four times and pluralised wrong in one of them.
 */
export function days(n) {
  return `${n} ${n === 1 ? 'day' : 'days'}`
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/**
 * "2026-08-05" -> "5 Aug". Parsed by SPLITTING THE STRING, never with
 * `new Date("2026-08-05")` — that parses as UTC midnight and renders as the
 * 4th in any timezone west of Greenwich, and as the 5th here only by luck.
 * The server sends a calendar date with no time and no zone; treating it as an
 * instant is how an expense moves a day.
 */
export function shortDate(iso) {
  const [, m, d] = iso.split('-')
  return `${Number(d)} ${MONTHS[Number(m) - 1]}`
}

/**
 * "2026-08-05" -> "Wednesday, 5 August 2026", for a screen-reader label where
 * the short form would be ambiguous. Built from the same split, then handed a
 * UTC date purely to name the weekday — the components are already correct, so
 * no shift can occur.
 */
export function longDate(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  const weekday = new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-US', {
    weekday: 'long', timeZone: 'UTC',
  })
  return `${weekday}, ${Number(d)} ${MONTHS[m - 1]} ${y}`
}
