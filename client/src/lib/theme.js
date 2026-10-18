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
