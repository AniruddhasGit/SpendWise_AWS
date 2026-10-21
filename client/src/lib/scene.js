import { useEffect, useState } from 'react'
import { flushSync } from 'react-dom'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Lenis from 'lenis'
import { stored } from './theme.js'

/**
 * The signed-out scene: the landing page and the sign-in page (SW-ADR-160).
 *
 * The two pages are one world, the money tree in its fog, so they share one
 * theme and one switch, and the tree is carried from one to the other.
 */

gsap.registerPlugin(ScrollTrigger)

// ── the scene's theme ──────────────────────────────────────────────────────
// Dark unless the person chose light. "System", the app's default, means
// dark here: the owner wants the scene dark by default.
export function sceneTheme() {
  return stored() === 'light' ? 'light' : 'dark'
}

/** Paints the document in the scene's theme without saving a choice, so the
    sign-in card and its inputs use the same colours as the scene around them. */
export function paintScene(theme) {
  document.documentElement.setAttribute('data-theme', theme)
}

// ── is the server awake? ───────────────────────────────────────────────────
// On the always-on front, the API sits behind a free server that sleeps.
// The question is asked of `/api/auth/me`, the call the app makes first
// anyway: any JSON answer (200 or the signed-out 401) means the server is up,
// while a sleeping one answers through the front with the host's own HTML
// page, or not at all. It is NOT asked of `/healthz`: ad-blockers (Brave's
// Shields, uBlock lists) block URLs named like health checks, and a blocked
// check left those visitors on "Almost there" for ever (2026-10-21). Asked only
// while a visitor is waiting, and never again once it answers: no keep-awake
// ping.
const WAKE_EVERY_MS = 2500
const ASK_TIMEOUT_MS = 12000
// Requests that fail before any answer, and fast (blocked, offline, refused),
// are not a sleeping server: after this many in a row the site opens anyway
// and its own calls show any real error, rather than trapping the visitor.
const GIVE_UP_AFTER = 3

async function awake() {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), ASK_TIMEOUT_MS)
  try {
    const res = await fetch('/api/auth/me', {
      cache: 'no-store', credentials: 'same-origin', signal: ctrl.signal,
    })
    const type = res.headers.get('content-type') || ''
    return type.includes('application/json') ? 'up' : 'asleep'
  } catch (err) {
    // an abort is our own timeout: the server is still waking up
    return err?.name === 'AbortError' ? 'asleep' : 'failed'
  } finally {
    clearTimeout(timer)
  }
}

/** True once the server answers. `since` is when the waiting began. */
export function useServerReady() {
  const [ready, setReady] = useState(false)
  const [since] = useState(() => Date.now())
  useEffect(() => {
    let live = true
    let timer = 0
    let failures = 0
    const ask = async () => {
      const state = await awake()
      failures = state === 'failed' ? failures + 1 : 0
      if (state === 'up' || failures >= GIVE_UP_AFTER) { if (live) setReady(true); return }
      if (live) timer = setTimeout(ask, WAKE_EVERY_MS)
    }
    ask()
    return () => { live = false; clearTimeout(timer) }
  }, [])
  return { ready, since }
}

// ── carrying the tree between the pages ────────────────────────────────────
// The browser's own View Transitions: the tree and the fog are named in CSS
// (`sw-tree`, `sw-fog`), so the browser morphs them from where they stood on
// the old page to where they stand on the new one. Everything else is handled
// by the pages' own exit and entrance animations.
//
// `arrive` names an element the new page must show before the morph starts
// (the dashboard draws its tree only once its data is in). The old page stays
// frozen on screen until it appears, at most `ARRIVE_MAX_MS`; past that the
// tree simply fades across instead of gliding.
const ARRIVE_MAX_MS = 2500
// elements whose own CSS entrance is suppressed while they are carried in
const CARRIED = '.dash-tree, .state-first-run'

function appeared(selector) {
  return new Promise((resolve) => {
    const t0 = performance.now()
    const look = () => {
      if (document.querySelector(selector) || performance.now() - t0 > ARRIVE_MAX_MS) resolve()
      // a timer, not requestAnimationFrame: rendering is paused while a view
      // transition waits on its update, and frame callbacks may not run
      else setTimeout(look, 30)
    }
    look()
  })
}

export function carryAcross(update, { arrive = null } = {}) {
  if (!document.startViewTransition) { update(); return Promise.resolve() }
  const root = document.documentElement
  // while carrying, the new page's own entrance on the carried element is off:
  // the browser captures it mid-entrance otherwise (invisible)
  root.setAttribute('data-carrying', '')
  const vt = document.startViewTransition(async () => {
    flushSync(update)
    if (arrive) await appeared(arrive)
  })
  return vt.finished.catch(() => {}).finally(() => {
    // Lifting the override would restart the CSS entrance it suppressed, so
    // the carried elements keep it off for as long as they are on screen.
    document.querySelectorAll(CARRIED).forEach((el) => el.classList.add('sw-carried'))
    root.removeAttribute('data-carrying')
  })
}

// ── smooth scroll, everywhere ──────────────────────────────────────────────
// Lenis on GSAP's ticker, so ScrollTrigger and the scroll share one loop.
let lenis = null
export function startSmoothScroll() {
  if (lenis) return lenis
  lenis = new Lenis({ lerp: 0.1, wheelMultiplier: 1, smoothWheel: true })
  lenis.on('scroll', ScrollTrigger.update)
  gsap.ticker.add((time) => lenis.raf(time * 1000))
  gsap.ticker.lagSmoothing(0)
  return lenis
}

export function scrollToTop() {
  if (lenis) lenis.scrollTo(0, { immediate: true })
  else window.scrollTo(0, 0)
}
