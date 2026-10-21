import { longDate, dollars } from '../lib/money.js'

/**
 * The per-day bar chart.
 *
 * `DESIGN-SYSTEM.md §5.2`: **`aria-hidden="true"` decoration inside a labelled
 * container.** Its accessible data representation is the date-grouped entry
 * list already on the page — the same numbers, already reachable. Marking each
 * bar up as a data point would make a screen reader read thirty-one values
 * that are about to be read again below.
 *
 * Every day in the range gets a bar, including the empty ones. A chart that
 * skips empty days compresses a fortnight of nothing into a gap you cannot
 * see, and the shape of a month's spending is most of what this is for.
 */
export default function DayBars({ days }) {
  const peak = days.reduce((m, d) => Math.max(m, d.total_paise), 0)

  return (
    <figure className="daybars-wrap">
      <div className="daybars" aria-hidden="true" data-testid="daybars">
        {days.map((d) => (
          <div
            key={d.date}
            className="daybar"
            data-empty={d.total_paise === 0 ? 'true' : 'false'}
            data-peak={peak > 0 && d.total_paise === peak ? 'true' : undefined}
            // A day with spending never renders as nothing: 2% is the floor, so
            // $5 on an otherwise $5,000 day is still a visible mark. A zero day
            // renders as the 2% stub in the border colour, which reads as the
            // baseline rather than as a tiny amount.
            style={{ height: peak > 0 ? `${Math.max(2, (d.total_paise / peak) * 100)}%` : '2%' }}
            title={`${longDate(d.date)}: ${dollars(d.total_paise)}`}
          />
        ))}
      </div>
      <figcaption className="entry-meta">
        Daily spending{peak > 0 ? `, tallest bar ${dollars(peak)}` : ''}
      </figcaption>
    </figure>
  )
}
