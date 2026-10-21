/**
 * Appearance. Three states, not two.
 *
 * `SW-ADR-147`: the design system declares dark twice — a
 * `prefers-color-scheme` media query (the DEFAULT, so a person whose system is
 * dark never sees a white flash before this file runs) and a
 * `:root[data-theme]` override (what this writes).
 *
 * So the control has three positions: **System**, **Light**, **Dark**.
 * "System" is the absence of the attribute, not a third value — writing
 * `data-theme="system"` would match neither selector and silently mean light.
 */

const KEY = 'spendwise.theme'
export const THEMES = ['system', 'light', 'dark']

export function stored() {
  try {
    const v = localStorage.getItem(KEY)
    return THEMES.includes(v) ? v : 'system'
  } catch {
    // Private browsing throws on localStorage in some browsers. A preference
    // is not worth a blank page.
    return 'system'
  }
}

export function apply(theme) {
  const root = document.documentElement
  if (theme === 'system') root.removeAttribute('data-theme')
  else root.setAttribute('data-theme', theme)
  try {
    localStorage.setItem(KEY, theme)
  } catch { /* see above */ }
  syncThemeColor(theme)
}

/**
 * The browser's own chrome (the phone status bar, the tab strip) is coloured
 * by `<meta name="theme-color" media="(prefers-color-scheme: …)">` in
 * index.html. Those follow the OS, so a forced theme would leave a light bar
 * over a dark page. While a theme is forced, both tags carry its paper; on
 * "System" they get their original colours back.
 */
function syncThemeColor(theme) {
  const metas = document.querySelectorAll('meta[name="theme-color"]')
  if (!metas.length) return
  const paper = theme === 'system'
    ? null
    : getComputedStyle(document.documentElement).getPropertyValue('--sw-paper').trim()
  metas.forEach((m) => {
    if (!m.dataset.original) m.dataset.original = m.getAttribute('content') || ''
    m.setAttribute('content', paper || m.dataset.original)
  })
}

/** What is actually on screen right now — `system` resolved against the OS. */
export function effective(theme) {
  if (theme !== 'system') return theme
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * Switch theme the way the owner's reference reel does: a liquid blob of the
 * new theme grows from the control that was pressed and floods the page
 * (the View Transitions API; the old page is a still snapshot underneath).
 *
 * Instant, with no blob, when: the browser has no View Transitions, motion is
 * reduced, the press came from a keyboard (`detail === 0`: keyboard actions are
 * never animated here), or the change does not alter what is painted (light
 * to System on a light device). The choice is SAVED before the animation, so a
 * reload mid-flood keeps it.
 */
export function switchTheme(theme, event) {
  const before = effective(currentTheme())
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  const pointer = event && event.detail > 0
  if (!document.startViewTransition || reduce || !pointer || before === effective(theme)) {
    apply(theme)
    return
  }
  try { localStorage.setItem(KEY, theme) } catch { /* apply() retries */ }
  const x = event.clientX
  const y = event.clientY
  const vt = document.startViewTransition(() => apply(theme))
  vt.ready.then(() => {
    document.documentElement.animate(
      { clipPath: blobFrames(x, y, window.innerWidth, window.innerHeight) },
      { duration: 950, easing: 'linear', pseudoElement: '::view-transition-new(root)' },
    )
  }).catch(() => { /* skipped transition: the theme is applied regardless */ })
}

function currentTheme() {
  return document.documentElement.getAttribute('data-theme') || 'system'
}

/**
 * The flood's outline at each step: a closed curve around (x, y) whose radius
 * ripples with three slow waves, so its front looks poured rather than drawn
 * with a compass. Every frame has the same commands, so the browser can
 * interpolate between them. It ends far past the farthest corner, ripples
 * included, so the last frame covers the whole window.
 */
function blobFrames(x, y, w, h) {
  const far = Math.max(Math.hypot(x, y), Math.hypot(w - x, y), Math.hypot(x, h - y), Math.hypot(w - x, h - y))
  const N = 36
  const STEPS = 30
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)
  const frames = []
  for (let k = 0; k <= STEPS; k += 1) {
    const t = k / STEPS
    const R = Math.max(1, ease(t) * far * 1.45)
    const pts = []
    for (let i = 0; i < N; i += 1) {
      const a = (i / N) * Math.PI * 2
      const ripple = 0.17 * Math.sin(3 * a + t * 5.2) + 0.09 * Math.sin(5 * a - t * 7.1 + 1.3)
        + 0.05 * Math.sin(8 * a + t * 3.3)
      const r = R * (1 + ripple)
      pts.push([x + Math.cos(a) * r, y + Math.sin(a) * r])
    }
    // a smooth closed curve: quadratic segments through the midpoints
    const mid = (p, q) => [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2]
    const f = (n) => n.toFixed(1)
    let d = `M ${mid(pts[N - 1], pts[0]).map(f).join(' ')}`
    for (let i = 0; i < N; i += 1) {
      const m = mid(pts[i], pts[(i + 1) % N])
      d += ` Q ${f(pts[i][0])} ${f(pts[i][1])} ${f(m[0])} ${f(m[1])}`
    }
    frames.push(`path('${d} Z')`)
  }
  return frames
}

/**
 * Applied BEFORE React mounts, from `main.jsx`.
 *
 * Doing it in an effect means the first paint uses the media query and then
 * flips — a white flash on every load for anyone who chose dark while their
 * system is light. The attribute has to be on `<html>` before the first paint,
 * and the first paint happens before any component renders.
 */
export function boot() {
  apply(stored())
}
