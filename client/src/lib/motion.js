/**
 * Motion + money-figure helpers. No library (SW-ADR-016): matchMedia,
 * requestAnimationFrame, CSS transitions and React's own hooks.
 *
 *   usePrefersReducedMotion()   live boolean
 *   useFinePointer()            live boolean: (hover: hover) and (pointer: fine)
 *   prefersReducedMotion()      non-hook read, for handlers and effects
 *   staggerStyle(i, max=8)      style object for one item of a staggered list
 *   tokenMs(name)               a --sw-dur-* token in milliseconds, for JS
 *   splitMoney(text)            "$7,581.00" -> { sign, cur, int, frac }
 *   <Money paise | text />      a figure with the dollar sign and paise styled
 *   <CountUp value format />    counts to its value on mount / change
 *   <Odometer value format />   rolls each digit to its new value on change
 *   <RouteFade viewKey>         remounts + settles its child on navigation
 *
 * THE RULE ALL THREE FIGURE COMPONENTS KEEP: the element's `innerText` is the
 * exact final formatted value on every frame. Browser tests read totals the
 * instant they render (`get_by_test_id("total").inner_text()`), and a screen
 * reader must never hear an intermediate figure. Ticking / rolling digits are
 * painted by CSS generated content from data attributes, which is neither in
 * innerText nor in the accessibility tree.
 *
 * Money is integer paise (CONSTITUTION Art V.1). Formatting is ALWAYS
 * lib/money.js; nothing here formats a number itself.
 *
 * This is a `.js` file, so components are built with createElement, not JSX.
 */
import { createElement, useEffect, useRef, useSyncExternalStore } from 'react'
import { dollars } from './money.js'

const h = createElement
const REDUCED = '(prefers-reduced-motion: reduce)'
const FINE = '(hover: hover) and (pointer: fine)'

function mediaStore(query) {
  const get = () => (typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia(query).matches
    : false)
  const subscribe = (notify) => {
    if (typeof window === 'undefined' || !window.matchMedia) return () => {}
    const mq = window.matchMedia(query)
    mq.addEventListener('change', notify)
    return () => mq.removeEventListener('change', notify)
  }
  return { get, subscribe }
}

const reducedStore = mediaStore(REDUCED)
const fineStore = mediaStore(FINE)

/** True while the person has asked the OS for reduced motion. Live. */
export function usePrefersReducedMotion() {
  return useSyncExternalStore(reducedStore.subscribe, reducedStore.get, () => false)
}

/** True on a device with a real hovering pointer (not touch). Live. */
export function useFinePointer() {
  return useSyncExternalStore(fineStore.subscribe, fineStore.get, () => false)
}

/** Non-hook read, for event handlers and effects. */
export function prefersReducedMotion() {
  return reducedStore.get()
}

/**
 * Style for item `i` of a staggered list. `.sw-stagger` already numbers its
 * first eight children in CSS; use this when the items are not direct
 * children, or are rendered by `.map()` inside wrappers.
 *
 *   <li className="sw-enter" style={staggerStyle(i)}>
 */
export function staggerStyle(i, max = 8) {
  return { '--sw-delay': `calc(${Math.min(Math.max(i, 0), max)} * var(--sw-stagger))` }
}

/** Read a duration token (`--sw-dur-count` -> 900). Falls back to `fallback`. */
export function tokenMs(name, fallback = 0) {
  try {
    const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
    const n = parseFloat(raw)
    if (Number.isNaN(n)) return fallback
    return raw.endsWith('ms') ? n : raw.endsWith('s') ? n * 1000 : n
  } catch {
    return fallback
  }
}

// ── money figures ───────────────────────────────────────────────────────────
const MONEY_RE = /^(-?)(\$?)([\d,]+)(\.\d+)?$/

/**
 * Split a formatted figure into its parts, WITHOUT reformatting it:
 *   "$7,581.00"  -> { sign: '',  cur: '$', int: '7,581', frac: '.00' }
 *   "-$12.50"    -> { sign: '-', cur: '$', int: '12',    frac: '.50' }
 * Anything else (a percentage, "5 days") returns null: render it as is.
 * Concatenating the parts always gives back `text` exactly.
 */
export function splitMoney(text) {
  if (typeof text !== 'string') return null
  const m = text.match(MONEY_RE)
  if (!m) return null
  return { sign: m[1], cur: m[2], int: m[3], frac: m[4] || '' }
}

// The parts as inline spans with NO whitespace between them, so innerText is
// the formatter's string byte for byte.
function moneyParts(text) {
  const p = splitMoney(text)
  if (!p) return [text]
  const out = []
  if (p.sign) out.push(p.sign)
  if (p.cur) out.push(h('span', { key: 'c', className: 'sw-money-cur' }, p.cur))
  out.push(p.int)
  if (p.frac) out.push(h('span', { key: 'f', className: 'sw-money-frac' }, p.frac))
  return out
}

/**
 * <Money paise={758100} />            -> $7,581.00, dollar sign and paise styled
 * <Money text="$7,581.00" />          -> the same, from an already-formatted string
 * <Money paise={n} sign />            -> "+$…" for a positive amount (income)
 * Extra props (className, data-testid, aria-*) go on the root span.
 */
export function Money({ paise, text, sign = false, className = '', ...rest }) {
  let shown = text ?? dollars(paise)
  if (shown == null) return null
  if (sign && typeof paise === 'number' && paise > 0) shown = `+${shown}`
  const parts = sign && shown.startsWith('+')
    ? ['+', ...moneyParts(shown.slice(1))]
    : moneyParts(shown)
  return h('span', { ...rest, className: `sw-money ${className}`.trim() }, ...parts)
}

// Exponential ease-out: fast start, long settle — what a number "landing" feels like.
const easeOutExpo = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t))

/**
 * Drive a `.sw-countup` element. Intermediate figures are written into the
 * ticker parts' `data-text` attributes (painted by CSS `::before`), and the
 * root is flagged `data-counting` while it runs. The real value is rendered by
 * React as text and is never touched here.
 *
 * Integers only. Intermediate values are rounded, and `format` (lib/money.js
 * for money) renders each one.
 */
export function useCountUp(rootRef, tickerRef, value, { format = String, duration, from = 0 } = {}) {
  const shown = useRef(null)

  useEffect(() => {
    const root = rootRef.current
    const ticker = tickerRef.current
    if (!root || !ticker || typeof value !== 'number' || !Number.isFinite(value)) return undefined

    const start = shown.current ?? from
    const skip = start === value
      || prefersReducedMotion()
      || (typeof document !== 'undefined' && document.hidden)
    if (skip) {
      shown.current = value
      root.removeAttribute('data-counting')
      return undefined
    }

    const [pCur, pInt, pFrac] = ticker.children
    const paint = (v) => {
      const text = format(v)
      const p = splitMoney(text)
      if (p && pCur) {
        pCur.setAttribute('data-text', p.sign + p.cur)
        pInt.setAttribute('data-text', p.int)
        pFrac.setAttribute('data-text', p.frac)
      } else if (pInt) {
        pCur?.setAttribute('data-text', '')
        pInt.setAttribute('data-text', text)
        pFrac?.setAttribute('data-text', '')
      }
    }

    const total = duration ?? tokenMs('--sw-dur-count', 900)
    let frame = 0
    let t0 = 0
    // `shown` tracks what is ON SCREEN, so an interrupted count (a new value
    // mid-flight, or StrictMode's mount-unmount-mount in dev) resumes from the
    // figure the person was looking at instead of jumping or skipping.
    shown.current = start
    const step = (now) => {
      if (!t0) t0 = now
      const p = Math.min((now - t0) / total, 1)
      const v = Math.round(start + (value - start) * easeOutExpo(p))
      shown.current = v
      paint(v)
      if (p < 1) frame = requestAnimationFrame(step)
      else root.removeAttribute('data-counting')
    }
    paint(start)
    root.setAttribute('data-counting', '')
    frame = requestAnimationFrame(step)
    return () => {
      cancelAnimationFrame(frame)
      root.removeAttribute('data-counting')
    }
    // `format` is usually an inline arrow; re-running on its identity would
    // restart the count on every parent render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])
}

/**
 * <CountUp value={paise} format={dollars} data-testid="total" className="sw-total" />
 *
 * Renders the FINAL formatted value as real text from the first frame (tests
 * and screen readers read that), and counts up visually over it. With a money
 * string the dollar sign and paise are styled (pass split={false} to opt out).
 * Extra props (data-testid, aria-*, title) go on the root span.
 */
export function CountUp({ value, format = dollars, duration, from = 0, split = true, className = '', ...rest }) {
  const rootRef = useRef(null)
  const tickerRef = useRef(null)
  useCountUp(rootRef, tickerRef, value, { format, duration, from })
  const text = format(value)
  return h(
    'span',
    { ...rest, ref: rootRef, className: `sw-countup sw-money ${className}`.trim() },
    h('span', { className: 'sw-countup-value' }, ...(split ? moneyParts(text) : [text])),
    h('span', { className: 'sw-countup-ticker', 'aria-hidden': 'true', ref: tickerRef },
      h('span', { className: 'sw-money-cur' }),
      h('span', null),
      h('span', { className: 'sw-money-frac' })),
  )
}

/**
 * <Odometer value={paise} format={dollars} className="card-value" />
 *
 * Each digit is a reel that ROLLS to its new value when `value` changes — a
 * mechanical counter, not a re-count from zero. Reels are keyed by place value
 * from the right, so $999 -> $1,000 rolls the units, tens and hundreds and
 * grows a new thousands reel instead of shifting every digit sideways.
 * Nothing rolls on first render (pair with <CountUp> for an entrance).
 *
 * The real value is a visually-hidden text node: it IS the innerText and the
 * accessible name. The reels are empty, aria-hidden spans painted by CSS.
 */
export function Odometer({ value, format = dollars, split = true, className = '', ...rest }) {
  const text = typeof value === 'number' ? format(value) : String(value ?? '')
  const p = split ? splitMoney(text) : null
  const reelOf = (str, cls, offsetFromRight) => {
    const chars = [...str]
    return chars.map((ch, i) => {
      const place = offsetFromRight + (chars.length - 1 - i)
      if (ch >= '0' && ch <= '9') {
        return h('span', {
          key: `d${place}`, className: 'sw-odo-d',
          style: { '--d': Number(ch), '--i': place },
        })
      }
      return h('span', { key: `c${place}${ch}`, className: 'sw-odo-c', 'data-c': ch })
    }).map((node) => (cls ? h('span', { key: `w${node.key}`, className: cls }, node) : node))
  }
  let reel
  if (p) {
    const fracLen = p.frac.length
    reel = [
      ...reelOf(p.sign, null, 1000),
      ...reelOf(p.cur, 'sw-money-cur', 900),
      ...reelOf(p.int, null, fracLen),
      ...reelOf(p.frac, 'sw-money-frac', 0),
    ]
  } else {
    reel = reelOf(text, null, 0)
  }
  return h(
    'span',
    { ...rest, className: `sw-odo ${split && p ? 'sw-money ' : ''}${className}`.trim() },
    h('span', { className: 'sw-odo-sr' }, text),
    h('span', { className: 'sw-odo-reel', 'aria-hidden': 'true' }, ...reel),
  )
}

/**
 * <RouteFade viewKey={view}>…the pane…</RouteFade>
 * Remounts its wrapper when `viewKey` changes, which replays `.sw-route`'s
 * settle (transform only; see motion.css). Extra props go on the wrapper div.
 */
export function RouteFade({ viewKey, className = '', children, ...rest }) {
  return h('div', { ...rest, key: viewKey, className: `sw-route ${className}`.trim() }, children)
}
