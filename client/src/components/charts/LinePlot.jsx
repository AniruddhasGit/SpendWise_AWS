import { useId, useRef, useState } from 'react'
import { longDate, rupees, shortDate } from '../../lib/money.js'
import { splitMoney } from '../../lib/motion.js'

/**
 * Spending over time. Hand-rolled SVG, and that is a decision.
 *
 * `SW-ADR-016` locks the stack and takes no UI framework; a charting library is
 * 40-140 kB to draw a polyline, and every one of them wants its own colour API,
 * which would put a second source of truth beside `tokens.css`. This is about
 * a hundred lines and every colour is a token.
 *
 * **Axes, and a cursor you can read.** The chart used to print only the first
 * and last date and no amounts at all, so a shape was all you got. It now has a
 * y axis (amounts at each gridline), an x axis (dates across the range) and a
 * pointer/keyboard/touch readout that snaps to the nearest day. Everything that
 * carries a label is HTML positioned in percentages OVER the plot frame, never
 * an SVG `<text>`: the SVG draws with `preserveAspectRatio="none"` so it
 * stretches, and stretched text distorts. The paths stretch; the words do not.
 *
 * `DESIGN-SYSTEM.md §5.2` used to keep this `aria-hidden` because a screen
 * reader reading thirty-one coordinates is not accessibility. The cursor is the
 * upgrade that replaces that stance: the SVG stays decorative, and a single
 * focusable control over the plot reads one day at a time with the arrow keys,
 * announced through a live region — the amounts in words, which a ring cannot do.
 */

// A compact Indian label for a y-axis tick: ₹20.8k, ₹1.0L, ₹3.2Cr — so a long
// amount never overflows the gutter. It is driven by the SAME `format` prop the
// caller passes, so the admin reuse (which passes a count, not money) keeps its
// plain number and never grows a rupee sign. Full precision stays in the tooltip.
function compact(value, format) {
  const full = format(value)
  const p = splitMoney(full)
  // Not money (a count, a percentage): show exactly what the formatter returned.
  if (!p || p.cur !== '₹') return full
  const n = Number(p.int.replace(/,/g, '')) + (p.frac ? Number(p.frac) : 0)
  const abbr = (v, suffix) => `${p.sign}₹${v.toFixed(1)}${suffix}`
  if (n >= 1e7) return abbr(n / 1e7, 'Cr')   // crore
  if (n >= 1e5) return abbr(n / 1e5, 'L')    // lakh
  if (n >= 1e3) return abbr(n / 1e3, 'k')    // thousand
  return `${p.sign}₹${p.int}`                // small: the whole rupees, grouped
}

export default function LinePlot({ days, cumulative = false, height = 180,
                                  format = rupees, noun = 'spending' }) {
  // A gradient needs a document-unique id: the dashboard draws two of these
  // and the admin overview a third. `useId` output contains colons, which are
  // not valid inside `url(#…)`, so they are stripped.
  const gradId = `plot-fill-${useId().replace(/:/g, '')}`

  // The focused/hovered day, by index. `null` when nothing is being read.
  const [active, setActive] = useState(null)
  const hitRef = useRef(null)
  // Tracks keyboard focus so a mouse leaving the plot does not wipe the readout
  // out from under a keyboard user who is still parked on a point.
  const focused = useRef(false)

  if (!days?.length) return null

  const W = 640
  const H = height
  // A real left gutter for the amounts and a bottom gutter for the dates. The
  // line never draws into them. These are viewBox units; because the SVG
  // stretches to the frame 1:1, a fraction of W/H is the same fraction of the
  // rendered frame, which is how every overlay below is placed.
  const PAD = { l: 70, r: 16, t: 14, b: 28 }

  let running = 0
  const points = days.map((d) => {
    running += d.total_paise
    return { date: d.date, value: cumulative ? running : d.total_paise }
  })
  const n = points.length
  const last = n - 1

  const peak = Math.max(1, ...points.map((p) => p.value))
  const stepX = (W - PAD.l - PAD.r) / Math.max(1, n - 1)
  const y = (v) => PAD.t + (1 - v / peak) * (H - PAD.t - PAD.b)
  const x = (i) => PAD.l + i * stepX
  // viewBox coordinate -> percentage across the frame, for the HTML overlays.
  const px = (i) => (x(i) / W) * 100
  const py = (v) => (y(v) / H) * 100

  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`)
  const area = `${line.join(' ')} L${x(last).toFixed(1)},${H - PAD.b} L${PAD.l},${H - PAD.b} Z`

  const busiest = points.reduce((a, b) => (b.value > a.value ? b : a), points[0])

  // Five horizontal gridlines including the baseline (f = 0, the x axis). Each
  // carries an amount in the gutter at exactly its height.
  const Y_FRACS = [1, 0.75, 0.5, 0.25, 0]
  const yticks = Y_FRACS.map((f) => ({
    f,
    top: py(peak * f),
    label: compact(Math.round(peak * f), format),
    axis: f === 0,
  }))

  // Up to five evenly spaced date ticks across the range. On a phone the two
  // in-between ones are dropped in CSS, leaving first / middle / last.
  const X_TICKS = 5
  const xticks = []
  const seen = new Set()
  for (let i = 0; i < X_TICKS; i++) {
    const idx = Math.round((i * last) / (X_TICKS - 1))
    if (seen.has(idx)) continue
    seen.add(idx)
    xticks.push({
      idx,
      optional: i !== 0 && i !== X_TICKS - 1 && i !== 2,
      edge: idx === 0 ? 'start' : idx === last ? 'end' : 'mid',
    })
  }

  // ── the readout ───────────────────────────────────────────────────────────
  const idxFromClientX = (clientX) => {
    const el = hitRef.current
    if (!el) return 0
    const r = el.getBoundingClientRect()
    if (r.width <= 0) return 0
    const frac = (clientX - r.left) / r.width
    return Math.max(0, Math.min(last, Math.round(frac * last)))
  }
  const onPointerMove = (e) => setActive(idxFromClientX(e.clientX))
  const onPointerDown = (e) => setActive(idxFromClientX(e.clientX))
  const onPointerLeave = () => { if (!focused.current) setActive(null) }
  const onFocus = () => { focused.current = true; setActive((p) => (p == null ? last : p)) }
  const onBlur = () => { focused.current = false; setActive(null) }
  const onKeyDown = (e) => {
    const cur = active == null ? last : active
    let next = cur
    switch (e.key) {
      case 'ArrowLeft': next = Math.max(0, cur - 1); break
      case 'ArrowRight': next = Math.min(last, cur + 1); break
      case 'Home': next = 0; break
      case 'End': next = last; break
      default: return
    }
    e.preventDefault()
    setActive(next)
  }

  const ap = active != null ? points[active] : null
  // The tooltip anchors itself away from the edges so it never clips: left edge
  // at the point near the start, right edge near the end, centred in between;
  // and it flips below the point when the point sits high in the frame.
  const tipX = ap ? (px(active) < 20 ? '0' : px(active) > 80 ? '-100%' : '-50%') : '-50%'
  const tipY = ap ? (py(ap.value) < 30 ? 'var(--sw-space-3)' : 'calc(-100% - var(--sw-space-3))') : '0'

  const summary = cumulative
    ? `Running total from ${shortDate(points[0].date)} to ${shortDate(points[last].date)}.`
    : `Daily ${noun} from ${shortDate(points[0].date)} to ${shortDate(points[last].date)}.`

  return (
    <figure className={`plot${cumulative ? ' plot-total' : ''}`}
            data-reading={ap ? 'true' : undefined}>
      <div className="plot-frame">
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none"
           className="plot-svg" aria-hidden="true" data-testid="line-plot"
           data-series={cumulative ? 'total' : 'daily'}>
        <defs>
          {/* The fill fades to nothing at the baseline, so the area reads as
              the line's shadow rather than as a second, solid shape. */}
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" className="plot-stop-top" stopColor="var(--sw-plot-line)" stopOpacity="0.22" />
            <stop offset="1" className="plot-stop-bottom" stopColor="var(--sw-plot-line)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Gridlines at 0/25/50/75/100% of the peak; the 0 line is the x axis
            and is drawn a touch stronger. The amounts sit beside them, in HTML. */}
        {yticks.map((t) => (
          <line key={t.f} className={`plot-grid${t.axis ? ' plot-axisline' : ''}`}
                x1={PAD.l} x2={W - PAD.r}
                y1={y(peak * t.f)} y2={y(peak * t.f)}
                vectorEffect="non-scaling-stroke" />
        ))}
        {/* Keyed on the range, so the wipe replays when the PERIOD changes
            (new data, new shape) and not on every re-render. */}
        <g className="plot-draw" key={`${points[0].date}:${n}`}>
          <path d={area} className="plot-area" fill={`url(#${gradId})`} />
          <path d={line.join(' ')} className="plot-line" fill="none"
                strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"
                vectorEffect="non-scaling-stroke" />
        </g>
      </svg>

      {/* Y axis: the amount at each gridline, compact so it never overflows the
          gutter. The container IS the gutter (its width is the plot's left
          inset), so the amounts right-align against the plot edge. Reused for
          counts unchanged — `compact` defers to `format`. */}
      <div className="plot-yaxis" aria-hidden="true" style={{ width: `${px(0)}%` }}>
        {yticks.map((t) => (
          <span key={t.f} className="plot-ytick sw-num" style={{ top: `${t.top}%` }}>
            {t.label}
          </span>
        ))}
      </div>

      {/* X axis: evenly spaced dates, each sat just under the baseline. The two
          in-between ones hide on a phone, leaving first / middle / last. */}
      <div className="plot-xaxis" aria-hidden="true">
        {xticks.map((t) => (
          <span key={t.idx} className="plot-xtick" data-edge={t.edge}
                data-optional={t.optional ? 'true' : undefined}
                style={{ left: `${px(t.idx)}%`, top: `${py(0)}%` }}>
            {shortDate(points[t.idx].date)}
          </span>
        ))}
      </div>

      {/* The peak bead — one dot on the busiest day, the point a person looks
          for first. It fades while the cursor is reading so the two never
          stack. HTML, not an SVG <circle>, so it keeps one on-screen size. */}
      <span className="plot-peak" aria-hidden="true"
            style={{ left: `${px(points.indexOf(busiest))}%`, top: `${py(busiest.value)}%` }} />

      {/* The cursor: a crosshair, a dot on the line, and a tooltip. All HTML,
          all pointer-events:none so the hit layer below keeps the events. */}
      {ap && (
        <>
          <span className="plot-crosshair" aria-hidden="true"
                style={{ left: `${px(active)}%`, top: `${PAD.t / H * 100}%`,
                         height: `${(H - PAD.t - PAD.b) / H * 100}%` }} />
          <span className="plot-cursor" aria-hidden="true"
                style={{ left: `${px(active)}%`, top: `${py(ap.value)}%` }} />
          <div className="plot-tip" aria-hidden="true"
               style={{ left: `${px(active)}%`, top: `${py(ap.value)}%`,
                        '--tip-tx': tipX, '--tip-ty': tipY }}>
            <span className="plot-tip-date">{longDate(ap.date)}</span>
            <span className="plot-tip-val sw-num">{format(ap.value)}</span>
          </div>
        </>
      )}

      {/* The hit + focus layer: the accessible control. It covers the plot area
          only (so x maps straight to a day), takes the pointer, the focus ring
          and the arrow keys, and is the one thing a screen reader lands on. */}
      <div ref={hitRef} className="plot-hit" role="img" tabIndex={0}
           aria-label={`${summary} Use the left and right arrow keys to read each day.`}
           style={{ left: `${PAD.l / W * 100}%`, right: `${PAD.r / W * 100}%`,
                    top: `${PAD.t / H * 100}%`, bottom: `${PAD.b / H * 100}%` }}
           onPointerMove={onPointerMove} onPointerDown={onPointerDown}
           onPointerLeave={onPointerLeave} onFocus={onFocus} onBlur={onBlur}
           onKeyDown={onKeyDown} />
      <span className="visually-hidden" aria-live="polite">
        {ap ? `${longDate(ap.date)}, ${format(ap.value)}` : ''}
      </span>
      </div>

      {/* The caption is FORMATTED BY THE CALLER. It was once hard-wired to
          `rupees()`, and the admin overview reuses this plot for a count of
          new accounts — so two signups rendered as "₹0.02", a currency symbol
          on a number that is not money, on the one screen that must never. */}
      <figcaption className="entry-meta">
        {cumulative
          ? `Running total, ending ${format(points[last].value)}`
          : `Daily ${noun}. Busiest day ${longDate(busiest.date)}, ${format(busiest.value)}`}
      </figcaption>
    </figure>
  )
}
