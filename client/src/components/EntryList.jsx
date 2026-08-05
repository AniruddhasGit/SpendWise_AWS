import { longDate, rupees, shortDate } from '../lib/money.js'

/**
 * The entry list, grouped by day.
 *
 * `DESIGN-SYSTEM.md §5.2` makes this the accessible representation of the bar
 * chart, so the grouping is not presentation — it is the thing that makes the
 * chart's information reachable without sight. The per-day subtotal shown
 * beside each date is the same number the bar encodes (E3-S4 AC3: the
 * subtotals sum exactly to the displayed total).
 */
export default function EntryList({ items, colorFor, onEdit, onDelete, busyId }) {
  const groups = []
  for (const item of items) {
    const last = groups[groups.length - 1]
    if (last && last.date === item.spent_on) last.items.push(item)
    else groups.push({ date: item.spent_on, items: [item] })
  }

  return (
    <div className="entries" data-testid="entries">
      {groups.map((g) => {
        const subtotal = g.items.reduce((s, i) => s + i.amount_paise, 0)
        return (
          <section key={g.date} aria-label={longDate(g.date)}>
            <h3 className="entry day-head">
              <span />
              <span className="entry-meta">{shortDate(g.date)}</span>
              <span className="entry-meta sw-num" data-testid={`subtotal-${g.date}`}>
                {rupees(subtotal)}
              </span>
              <span />
            </h3>
            <ul>
              {g.items.map((e) => (
                <li className="entry" key={e.id} data-testid={`entry-${e.id}`}>
                  {/* The dot repeats the ribbon's colour so a row can be traced
                      back to its band. It is `aria-hidden` because the category
                      NAME is right beside it — the colour carries no
                      information the text does not. */}
                  <span
                    className="entry-dot"
                    aria-hidden="true"
                    style={{ background: colorFor(e.category_id) }}
                  />
                  <div className="entry-main">
                    <div className="entry-desc">{e.description || 'No note'}</div>
                    <div className="entry-meta">
                      {e.category_name || 'Uncategorised'}
                    </div>
                  </div>
                  <div className="entry-amount sw-num">{rupees(e.amount_paise)}</div>
                  <div className="entry-actions">
                    <button
                      type="button"
                      className="icon-btn"
                      data-testid={`edit-${e.id}`}
                      onClick={() => onEdit(e)}
                      aria-label={`Edit ${rupees(e.amount_paise)} on ${longDate(e.spent_on)}`}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="icon-btn"
                      data-testid={`delete-${e.id}`}
                      aria-disabled={busyId === e.id ? 'true' : undefined}
                      onClick={() => onDelete(e)}
                      aria-label={`Delete ${rupees(e.amount_paise)} on ${longDate(e.spent_on)}`}
                    >
                      Delete
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
