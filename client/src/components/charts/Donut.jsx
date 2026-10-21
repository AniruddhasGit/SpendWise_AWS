import { dollars } from '../../lib/money.js'
import { Odometer } from '../../lib/motion.js'

/**
 * Spending by category, as a ring.
 *
 * The client asked for a pie; a donut is a pie with the middle back, and the
 * middle is where the total goes — which is the number people are actually
 * looking for when they look at a pie of their spending.
 *
 * **Drawn with `stroke-dasharray` on one circle per slice**, not with arc
 * paths. Arc maths has a genuine singularity at 100%: a single-category month
 * makes start and end coincide and the arc renders as *nothing*. A dash
 * pattern has no such case, and a single-category month is the commonest edge
 * this will meet.
 *
 * Like the ribbon, this is a **control**: each slice is a button, one tab stop
 * for the group, `aria-pressed` on the selection, and the same two cues
 * (`SW-ADR-118`). It filters the same state the ribbon does, so the two stay in
 * agreement by construction rather than by remembering.
 */
const R = 60
const C = 2 * Math.PI * R

export default function Donut({ buckets, selected, onSelect, total }) {
  if (!buckets?.length) return null

  const key = (b) => (b.category_id === null ? 'none' : b.category_id)
  const isSelected = (b) => selected !== null && key(b) === selected

  let offset = 0
  const slices = buckets.map((b) => {
    const length = (b.percent / 100) * C
    const slice = { ...b, length, offset }
    offset += length
    return slice
  })

  return (
    <div className="donut-wrap">
      <div className="donut" data-filtering={selected !== null ? 'true' : 'false'}>
        <svg viewBox="0 0 160 160" className="donut-svg" role="group"
             aria-label="Spending by category" data-testid="donut">
          {/* The empty ring under the slices: a hairline track, so a month
              whose slices do not quite close (rounding) still reads as a
              whole, and the ring has a shape while the slices draw in. */}
          <circle className="donut-track" cx="80" cy="80" r={R} fill="none"
                  strokeWidth="20" aria-hidden="true" />
          {slices.map((s) => (
            <circle
              key={key(s)}
              className="slice"
              data-testid={`slice-${key(s)}`}
              data-category={key(s)}
              cx="80" cy="80" r={R}
              fill="none"
              stroke={s.color}
              strokeWidth={isSelected(s) ? 26 : 20}
              strokeDasharray={`${s.length} ${C - s.length}`}
              strokeDashoffset={-s.offset}
              /* -90deg so the first slice starts at twelve o'clock. A ring
                 that starts at three reads as rotated, not as a chart. */
              transform="rotate(-90 80 80)"
              role="button"
              tabIndex={-1}
              aria-pressed={isSelected(s)}
              aria-label={`${s.category_name}: ${dollars(s.total_paise)}, ${s.percent}% of total`}
              onClick={() => onSelect(isSelected(s) ? null : key(s))}
            />
          ))}
        </svg>
        <div className="donut-centre" aria-hidden="true">
          {/* Rolls digit by digit when a slice filters the total. */}
          <Odometer value={total} className="donut-total"
                    style={{ '--donut-chars': dollars(total).length }} />
          <span className="entry-meta">
            {selected !== null ? 'filtered' : 'total'}
          </span>
        </div>
      </div>

      {/* The legend is the KEYBOARD path. An SVG `<circle role="button">` is
          reachable in some browsers and not others, so the real control is
          here — native buttons, the same aria-pressed state, and the amounts
          spelled out, which a ring cannot do. */}
      <ul className="donut-legend">
        {buckets.map((b) => (
          <li key={key(b)}>
            <button
              type="button"
              className="legend-btn"
              data-testid={`legend-${key(b)}`}
              aria-pressed={isSelected(b)}
              onClick={() => onSelect(isSelected(b) ? null : key(b))}
            >
              {/* A coin, not a bare square: the rim is what keeps a pale
                  category colour visible against the card (3:1). */}
              <span className="legend-swatch sw-swatch" style={{ '--coin': b.color }}
                    aria-hidden="true" />
              <span className="legend-name">{b.category_name}</span>
              <span className="legend-amount sw-num">{dollars(b.total_paise)}</span>
              <span className="legend-pct sw-num">{b.percent}%</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
