import { useEffect, useRef } from 'react'
import { longDate, dollars, shortDate } from '../lib/money.js'
import { Money, staggerStyle } from '../lib/motion.js'

/**
 * The entry list, grouped by day.
 *
 * `DESIGN-SYSTEM.md §5.2` makes this the accessible representation of the bar
 * chart, so the grouping is not presentation — it is the thing that makes the
 * chart's information reachable without sight. The per-day subtotal shown
 * beside each date is the same number the bar encodes (E3-S4 AC3: the
 * subtotals sum exactly to the displayed total).
 *
 * Drawn as a LEDGER (screens/expenses.css): each day is a receipt section
 * with the date, a dotted leader and the day's subtotal; each row is a coin,
 * the note and category, then the amount on one shared right-hand edge.
 * Every figure renders through <Money>, whose innerText is exactly what
 * dollars() returns, so nothing a test or a screen reader reads has changed.
 *
 * `freshId` is the expense just added (SW-ADR-156): its row carries a "New"
 * tag until it has been on screen for a moment, then `onSeen` clears it.
 */
export default function EntryList({ items, colorFor, onEdit, onDelete, busyId, freshId = null, onSeen }) {
  const rootRef = useRef(null)
  useEffect(() => {
    if (freshId == null || !onSeen) return undefined
    const row = rootRef.current?.querySelector(`[data-testid="entry-${freshId}"]`)
    if (!row) return undefined
    let timer = 0
    const io = new IntersectionObserver(([e]) => {
      clearTimeout(timer)
      if (e.isIntersecting) timer = setTimeout(onSeen, 2400)
    }, { threshold: 0.6 })
    io.observe(row)
    return () => { clearTimeout(timer); io.disconnect() }
  }, [freshId, onSeen, items])

  const groups = []
  for (const item of items) {
    const last = groups[groups.length - 1]
    if (last && last.date === item.spent_on) last.items.push(item)
    else groups.push({ date: item.spent_on, items: [item] })
  }

  // One running index across days, so the stagger reads top to bottom as a
  // single list (capped at 8 by staggerStyle: the ninth row never waits).
  let row = 0

  return (
    <div className="entries ledger" data-testid="entries" ref={rootRef}>
      {groups.map((g) => {
        const subtotal = g.items.reduce((s, i) => s + i.amount_paise, 0)
        return (
          <section key={g.date} className="ledger-day" aria-label={longDate(g.date)}>
            <h3 className="day-head sw-leader">
              <span className="day-date">{shortDate(g.date)}</span>
              <Money paise={subtotal} className="day-subtotal"
                     data-testid={`subtotal-${g.date}`} />
            </h3>
            <ul className="ledger-rows">
              {g.items.map((e) => (
                <li className={`entry sw-enter${e.id === freshId ? ' is-fresh' : ''}`}
                    key={e.id} data-testid={`entry-${e.id}`}
                    style={staggerStyle(row++)}>
                  {/* The coin repeats the ribbon's colour so a row can be
                      traced back to its band. It is `aria-hidden` because the
                      category NAME is right beside it; the colour carries no
                      information the text does not. `.sw-swatch` adds the
                      3:1 rim that a bare colour lacks on a light surface. */}
                  <span
                    className="entry-dot sw-swatch"
                    aria-hidden="true"
                    style={{ '--coin': colorFor(e.category_id) }}
                  />
                  <div className="entry-main">
                    <div className="entry-desc">{e.description || 'No note'}</div>
                    <div className="entry-meta">
                      {e.category_name || 'Uncategorised'}
                      {e.id === freshId && <span className="entry-fresh">New</span>}
                    </div>
                  </div>
                  <Money paise={e.amount_paise} className="entry-amount sw-neg" />
                  <div className="entry-actions">
                    <button
                      type="button"
                      className="icon-btn"
                      data-testid={`edit-${e.id}`}
                      onClick={() => onEdit(e)}
                      aria-label={`Edit ${dollars(e.amount_paise)} on ${longDate(e.spent_on)}`}
                    >
                      <PencilIcon />
                    </button>
                    <button
                      type="button"
                      className="icon-btn icon-btn-danger"
                      data-testid={`delete-${e.id}`}
                      aria-disabled={busyId === e.id ? 'true' : undefined}
                      onClick={() => onDelete(e)}
                      aria-label={`Delete ${dollars(e.amount_paise)} on ${longDate(e.spent_on)}`}
                    >
                      <TrashIcon />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}

// Hand-drawn, per the system's icon rule: 24 viewBox, 1.75 stroke,
// currentColor, decorative (the button carries the accessible name).
export function PencilIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M4 20h4L19 9a2.83 2.83 0 0 0-4-4L4 16v4Z" />
      <path d="m13.5 6.5 4 4" />
    </svg>
  )
}

export function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M4 7h16" />
      <path d="M9 7V4.5h6V7" />
      <path d="M6.5 7 7.5 20h9l1-13" />
      <path d="M10 11v5.5M14 11v5.5" />
    </svg>
  )
}
