import { useEffect, useRef, useState } from 'react'
import { dollars } from '../lib/money.js'

/**
 * The category ribbon — **both the chart and the filter** (`SRC-001 §9.2`).
 *
 * `SW-ADR-117` and `DESIGN-SYSTEM.md §5.1` make it a CONTROL rather than a
 * picture, and every rule below is one of theirs:
 *
 * - container `role="group"`, `aria-label="Spending by category"`
 * - each band is a native `<button>` — not a div with a click handler
 * - **one Tab stop for the whole ribbon** (roving tabindex); arrows move
 *   between bands, Home/End jump to the ends, Enter/Space toggles, Escape
 *   clears
 * - accessible name per band: `"{Category}: ${amount}, {pct}% of total"`
 * - `aria-pressed` reflects selection
 * - selection is **never colour-only** — the chosen band gains an inset marker
 *   AND the others dim (the CSS does this; both cues, so it survives colour
 *   blindness and a monochrome screen)
 * - geometry stays true-proportion (`SW-ADR-055`): a sliver band is still
 *   reachable by arrow key and still announces its full name
 *
 * And the one that is behaviour rather than presentation: selecting a band
 * re-scopes the total, count, average, day bars and list — but **not the
 * ribbon**, which stays whole-period so proportions remain visible and other
 * bands stay reachable (`SW-ADR-109`). This component therefore renders from
 * the UNFILTERED summary, always. The dashboard holds both.
 */
export default function Ribbon({ buckets, selected, onSelect }) {
  // The roving tabindex cursor: which band is the ribbon's single tab stop.
  // Distinct from `selected` — you arrow onto a band without filtering by it,
  // which is what makes one Tab press able to leave the group.
  const [cursor, setCursor] = useState(0)
  const refs = useRef([])
  const shouldFocus = useRef(false)

  const total = buckets.reduce((sum, b) => sum + b.total_paise, 0)

  useEffect(() => {
    // Only steal focus when the cursor moved BY KEYBOARD. Focusing on every
    // render would drag focus back into the ribbon whenever the summary
    // reloads — including while someone is typing in the add-expense panel.
    if (shouldFocus.current) {
      shouldFocus.current = false
      refs.current[cursor]?.focus()
    }
  }, [cursor])

  useEffect(() => {
    // A band can disappear when the period changes. Clamp rather than leaving
    // the cursor past the end, where arrow keys would do nothing.
    if (cursor > buckets.length - 1) setCursor(Math.max(0, buckets.length - 1))
  }, [buckets.length, cursor])

  const move = (next) => {
    shouldFocus.current = true
    setCursor(Math.max(0, Math.min(buckets.length - 1, next)))
  }

  const onKeyDown = (event) => {
    const keys = {
      ArrowRight: () => move(cursor + 1),
      ArrowLeft: () => move(cursor - 1),
      Home: () => move(0),
      End: () => move(buckets.length - 1),
      // Escape CLEARS the filter. It does not close anything — there is
      // nothing open — so it must not bubble to a dialog that is not there.
      Escape: () => onSelect(null),
    }
    const handler = keys[event.key]
    if (!handler) return
    event.preventDefault()
    handler()
  }

  if (!buckets.length) return null

  const key = (b) => (b.category_id === null ? 'none' : b.category_id)
  const isSelected = (b) => selected !== null && key(b) === selected

  return (
    <div className="ribbon-wrap">
      <div className="ribbon-head">
        <h2 className="ribbon-title" id="ribbon-title">Spending by category</h2>
        {selected !== null && (
          <button type="button" className="btn-link" onClick={() => onSelect(null)}>
            Clear filter
          </button>
        )}
      </div>

      <div
        className="ribbon"
        role="group"
        aria-labelledby="ribbon-title"
        data-filtering={selected !== null ? 'true' : 'false'}
        data-testid="ribbon"
        onKeyDown={onKeyDown}
      >
        {buckets.map((b, i) => (
          <button
            key={key(b)}
            type="button"
            ref={(el) => { refs.current[i] = el }}
            className="band"
            data-testid={`band-${key(b)}`}
            data-category={key(b)}
            // ONE tab stop for the whole ribbon. Every band but the cursor is
            // -1, so Tab enters once and the second Tab leaves (E3-S3 AC1).
            tabIndex={i === cursor ? 0 : -1}
            aria-pressed={isSelected(b)}
            // The band is a rectangle of colour with no text inside it, so the
            // accessible name is the ONLY name it has. `DESIGN-SYSTEM.md §5.1`
            // specifies this string exactly.
            aria-label={`${b.category_name}: ${dollars(b.total_paise)}, ${b.percent}% of total`}
            // TRUE PROPORTION. The percent the server computed, not one
            // recomputed here — the server's percentages sum to exactly 100 by
            // largest-remainder, and a second rounding would break that.
            style={{ width: `${b.percent}%`, background: b.color }}
            title={`${b.category_name} — ${dollars(b.total_paise)} (${b.percent}%)`}
            onFocus={() => setCursor(i)}
            onClick={() => onSelect(isSelected(b) ? null : key(b))}
          />
        ))}
      </div>

      {/* The legend is not decoration: at 0.4% a band is three pixels wide and
          the legend is the only place its name is readable with a mouse.
          `aria-hidden` because every one of these names is already on the
          band's accessible name — announcing both would double every item. */}
      <ul className="ribbon-legend" aria-hidden="true">
        {buckets.map((b) => (
          // The swatch is the coin's own ::before, with a rim, so a pale
          // category stays visible on the card.
          <li className="legend-item sw-coin" key={key(b)} style={{ '--coin': b.color }}
              title={`${b.category_name}: ${b.percent}%`}>
            <span className="legend-item-name">{b.category_name}</span>
            <span className="sw-num legend-item-pct">{b.percent}%</span>
          </li>
        ))}
      </ul>

      <p className="visually-hidden">
        {total > 0
          ? `Total across ${buckets.length} categories: ${dollars(total)}.`
          : 'No spending in this period.'}
      </p>
    </div>
  )
}
