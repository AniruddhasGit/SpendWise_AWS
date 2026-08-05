import { longDate, rupees, shortDate } from '../../lib/money.js'

/**
 * Spending over time. Hand-rolled SVG, and that is a decision.
 *
 * `SW-ADR-016` locks the stack and takes no UI framework; a charting library is
 * 40-140 kB to draw a polyline, and every one of them wants its own colour API,
 * which would put a second source of truth beside `tokens.css`. This is about
 * sixty lines and every colour is a token.
 *
 * `DESIGN-SYSTEM.md §5.2` governs it: **`aria-hidden` decoration inside a
 * labelled container**, because its accessible representation is the
 * date-grouped entry list already on the page. A screen reader reading
 * thirty-one coordinates is not accessibility.
 */
export default function LinePlot({ days, cumulative = false, height = 180,
                                  format = rupees, noun = 'spending' }) {
  if (!days?.length) return null

  const W = 640
  const H = height
  const PAD = { l: 8, r: 8, t: 12, b: 20 }

  let running = 0
  const points = days.map((d) => {
    running += d.total_paise
    return { date: d.date, value: cumulative ? running : d.total_paise }
  })

  const peak = Math.max(1, ...points.map((p) => p.value))
  const stepX = (W - PAD.l - PAD.r) / Math.max(1, points.length - 1)
  const y = (v) => PAD.t + (1 - v / peak) * (H - PAD.t - PAD.b)
  const x = (i) => PAD.l + i * stepX

  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`)
  const area = `${line.join(' ')} L${x(points.length - 1).toFixed(1)},${H - PAD.b} L${PAD.l},${H - PAD.b} Z`

  const busiest = points.reduce((a, b) => (b.value > a.value ? b : a), points[0])

  return (
    <figure className="plot">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none"
           className="plot-svg" aria-hidden="true" data-testid="line-plot">
        {/* Four gridlines, not ten. The chart answers "what shape was this
            month", and a dense grid invites reading exact values off it —
            which is what the entry list is for and does exactly. */}
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line key={f} x1={PAD.l} x2={W - PAD.r}
                y1={y(peak * f)} y2={y(peak * f)}
                stroke="var(--sw-plot-grid)" strokeWidth="1" />
        ))}
        <path d={area} fill="var(--sw-plot-fill)" />
        <path d={line.join(' ')} fill="none" stroke="var(--sw-plot-line)"
              strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"
              vectorEffect="non-scaling-stroke" />
        {/* One dot, on the peak. Thirty-one dots is noise; the peak is the
            single point a person looks for. */}
        <circle cx={x(points.indexOf(busiest))} cy={y(busiest.value)} r="3.5"
                fill="var(--sw-plot-line)" />
      </svg>

      <div className="plot-axis" aria-hidden="true">
        <span>{shortDate(points[0].date)}</span>
        <span>{shortDate(points[points.length - 1].date)}</span>
      </div>

      {/* The caption is FORMATTED BY THE CALLER. It was hard-wired to
          `rupees()`, and the admin overview reuses this plot for a count of
          new accounts — so two signups rendered as "₹0.02", a currency symbol
          on a number that is not money, on the one screen in the product that
          must never show any. */}
      <figcaption className="entry-meta">
        {cumulative
          ? `Running total, ending ${format(points[points.length - 1].value)}`
          : `Daily ${noun}. Busiest day ${longDate(busiest.date)}, ${format(busiest.value)}`}
      </figcaption>
    </figure>
  )
}
