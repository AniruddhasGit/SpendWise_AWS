import { useEffect, useId, useRef, useState } from 'react'
import { today } from '../lib/period.js'

/**
 * A date field whose calendar wears the app's theme (owner, 2026-10-21).
 *
 * The browser's own date popup cannot be styled: it painted a grey system
 * calendar over the emerald panel. So the native `<input type="date">` stays,
 * still typeable, still what the form submits and what the browser tests fill,
 * with its own picker icon hidden; a button beside it opens this calendar.
 *
 * Keyboard: the button opens it with focus on the chosen day; arrows move by
 * a day or a week, PageUp/PageDown by a month, Home/End to the week's ends,
 * Enter or Space picks, Escape closes and hands focus back to the button.
 */
const WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
  'August', 'September', 'October', 'November', 'December']

const pad = (n) => String(n).padStart(2, '0')
const iso = (y, m, d) => `${y}-${pad(m + 1)}-${pad(d)}`
function parse(value) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || '')
  return m ? { y: Number(m[1]), m: Number(m[2]) - 1, d: Number(m[3]) } : null
}
function shift(value, days) {
  const p = parse(value)
  const dt = new Date(Date.UTC(p.y, p.m, p.d + days))
  return iso(dt.getUTCFullYear(), dt.getUTCMonth(), dt.getUTCDate())
}
function shiftMonth(value, months) {
  const p = parse(value)
  const first = new Date(Date.UTC(p.y, p.m + months, 1))
  const y = first.getUTCFullYear(); const m = first.getUTCMonth()
  const last = new Date(Date.UTC(y, m + 1, 0)).getUTCDate()
  return iso(y, m, Math.min(p.d, last))
}
function spoken(value) {
  const p = parse(value)
  const wd = new Date(Date.UTC(p.y, p.m, p.d)).getUTCDay()
  return `${['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][wd]}, ${p.d} ${MONTHS[p.m]} ${p.y}`
}

export default function DatePicker({ id, name, value, onChange, required, invalid, describedBy }) {
  const [open, setOpen] = useState(false)
  const [focus, setFocus] = useState(() => value || today())
  const wrap = useRef(null)
  const button = useRef(null)
  const grid = useRef(null)
  const popId = useId()

  const set = (next) => onChange({ target: { value: next } })

  const show = () => { setFocus(parse(value) ? value : today()); setOpen(true) }
  const close = (refocus = true) => { setOpen(false); if (refocus) button.current?.focus() }

  // close on a press outside
  useEffect(() => {
    if (!open) return undefined
    const onDown = (e) => { if (!wrap.current?.contains(e.target)) close(false) }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  // keep focus on the active day, and the calendar in view
  useEffect(() => {
    if (!open) return
    grid.current?.querySelector(`[data-day="${focus}"]`)?.focus({ preventScroll: true })
    grid.current?.closest('.date-pop')?.scrollIntoView({ block: 'nearest' })
  }, [open, focus])

  const pick = (day) => { set(day); close() }

  const onKey = (e) => {
    const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }
    if (moves[e.key] !== undefined) { e.preventDefault(); setFocus((f) => shift(f, moves[e.key])) }
    else if (e.key === 'PageUp') { e.preventDefault(); setFocus((f) => shiftMonth(f, -1)) }
    else if (e.key === 'PageDown') { e.preventDefault(); setFocus((f) => shiftMonth(f, 1)) }
    else if (e.key === 'Home') {
      e.preventDefault()
      setFocus((f) => { const p = parse(f); return shift(f, -new Date(Date.UTC(p.y, p.m, p.d)).getUTCDay()) })
    } else if (e.key === 'End') {
      e.preventDefault()
      setFocus((f) => { const p = parse(f); return shift(f, 6 - new Date(Date.UTC(p.y, p.m, p.d)).getUTCDay()) })
    } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); close() }
  }

  const f = parse(focus) || parse(today())
  const startDay = new Date(Date.UTC(f.y, f.m, 1)).getUTCDay()
  const daysIn = new Date(Date.UTC(f.y, f.m + 1, 0)).getUTCDate()
  const cells = []
  for (let i = 0; i < 42; i += 1) {
    const day = shift(iso(f.y, f.m, 1), i - startDay)
    cells.push({ day, n: parse(day).d, inMonth: i >= startDay && i < startDay + daysIn })
  }
  const now = today()

  return (
    <div className="date-field" ref={wrap}>
      <input id={id} name={name} type="date" value={value} required={required}
             onChange={(e) => set(e.target.value)}
             aria-invalid={invalid ? 'true' : undefined} aria-describedby={describedBy} />
      <button type="button" className="date-open" ref={button}
              aria-label="Choose a date from a calendar" aria-haspopup="dialog"
              aria-expanded={open} aria-controls={open ? popId : undefined}
              onClick={() => (open ? close() : show())}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
             strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M4.5 6.5h15v13h-15zM4.5 10.5h15M8.5 4v4M15.5 4v4" />
        </svg>
      </button>

      {open && (
        <div className="date-pop" id={popId} role="dialog" aria-modal="false"
             aria-label={`Choose a date, ${MONTHS[f.m]} ${f.y}`} onKeyDown={onKey}>
          <div className="date-head">
            <button type="button" className="date-nav" aria-label="Previous month"
                    onClick={() => setFocus((x) => shiftMonth(x, -1))}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                   strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>
            </button>
            <span className="date-title" aria-live="polite">{MONTHS[f.m]} {f.y}</span>
            <button type="button" className="date-nav" aria-label="Next month"
                    onClick={() => setFocus((x) => shiftMonth(x, 1))}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                   strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg>
            </button>
          </div>
          <div className="date-grid" ref={grid}>
            {WEEKDAYS.map((w) => <span key={w} className="date-wd" aria-hidden="true">{w}</span>)}
            {cells.map((c) => (
              <button key={c.day} type="button" data-day={c.day}
                      className={`date-day${c.inMonth ? '' : ' is-out'}${c.day === now ? ' is-today' : ''}`}
                      aria-label={spoken(c.day) + (c.day === now ? ', today' : '')}
                      aria-pressed={c.day === value}
                      tabIndex={c.day === focus ? 0 : -1}
                      onClick={() => pick(c.day)}>
                {c.n}
              </button>
            ))}
          </div>
          <div className="date-foot">
            <button type="button" className="btn-link" onClick={() => pick(now)}>Today</button>
          </div>
        </div>
      )}
    </div>
  )
}
