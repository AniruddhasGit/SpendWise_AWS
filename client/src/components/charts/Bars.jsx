import { rupees } from '../../lib/money.js'

/**
 * A small horizontal bar chart — used for the day-of-week pattern and for the
 * admin's per-account activity.
 *
 * Horizontal, because the labels are words. A vertical chart with seven
 * weekday names underneath either truncates them or rotates them 45°, and both
 * are worse than turning the chart.
 */
export default function Bars({ rows, format = rupees, label, testId }) {
  if (!rows?.length) return null
  const peak = Math.max(1, ...rows.map((r) => r.value))

  return (
    <div className="bars" data-testid={testId} aria-label={label} role="img">
      {rows.map((r) => (
        <div className="bar-row" key={r.label}>
          <span className="bar-label">{r.label}</span>
          <span className="bar-track">
            <span className="bar-fill"
                  style={{ width: `${Math.max(1, (r.value / peak) * 100)}%` }} />
          </span>
          <span className="bar-value sw-num">{format(r.value)}</span>
        </div>
      ))}
      {/* The same numbers as text, for a screen reader — the chart itself is
          `role="img"` with a label, and this is what the label points at. */}
      <p className="visually-hidden">
        {rows.map((r) => `${r.label}: ${format(r.value)}`).join('. ')}
      </p>
    </div>
  )
}
