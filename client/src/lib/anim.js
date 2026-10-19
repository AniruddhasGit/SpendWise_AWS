/**
 * Shared framer-motion vocabulary (SW-ADR-156). Complements lib/motion.js,
 * which OWNS the figure components (<Money>/<CountUp>/<Odometer>) and the
 * reduced-motion / fine-pointer hooks, and keeps the invariant that a figure's
 * innerText is its exact final value on every frame. This file owns only the
 * Motion variants/transitions used by `m.*` components for the new premium
 * motion (hero, enter/exit, gestures, chart draw-ins).
 *
 * THE GLASS RULE (see styles/motion.css): on an element that has
 * `backdrop-filter` glass children, animate TRANSFORM ONLY (x/y/scale) — never
 * `opacity`/`filter` — or the element becomes the glass's backdrop root and the
 * frosting breaks for the whole animation. Use `riseTransformOnly`/`pageInOut`
 * on glass panes; `fadeRise`/`panelInOut` only where there is no glass child.
 *
 * Reduced motion is handled globally by <MotionConfig reducedMotion="user">;
 * `reveal()` is a belt-and-braces no-op for explicit opt-outs.
 */

// ── transitions ──────────────────────────────────────────────────────────────
export const spring = { type: 'spring', stiffness: 420, damping: 34, mass: 0.9 }
export const springSoft = { type: 'spring', stiffness: 120, damping: 18, mass: 1 }
export const springSnappy = { type: 'spring', stiffness: 700, damping: 30 }

// ── variants ─────────────────────────────────────────────────────────────────
// Non-glass only (fades opacity).
export const fadeRise = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: spring },
}
// Glass-safe: transform only, no opacity/filter.
export const riseTransformOnly = {
  hidden: { y: 8, scale: 0.985 },
  show: { y: 0, scale: 1, transition: spring },
}
// Staggered lists (mirrors .sw-stagger: 40ms/item).
export const staggerParent = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04, delayChildren: 0.02 } },
}
export const staggerChild = fadeRise

// AnimatePresence modal/panel — only where there is no glass-over-glass.
export const panelInOut = {
  hidden: { opacity: 0, y: 12, scale: 0.98 },
  show: { opacity: 1, y: 0, scale: 1, transition: spring },
  exit: { opacity: 0, y: 8, scale: 0.98, transition: { duration: 0.15 } },
}
// Route panes — transform only (glass-safe), mirrors .sw-route's settle.
export const pageInOut = {
  hidden: { y: 6 },
  show: { y: 0, transition: { duration: 0.24, ease: [0.2, 0, 0, 1] } },
  exit: { y: -4, transition: { duration: 0.16 } },
}

// ── gesture preset ───────────────────────────────────────────────────────────
// The tactile card/button feel. Spread onto an m.* element: <m.div {...hoverLift}>
export const hoverLift = {
  whileHover: { y: -3, transition: spring },
  whileTap: { scale: 0.97, transition: springSnappy },
}

// Belt-and-braces: a no-op variant when the caller already knows reduced motion.
export const reveal = (reduced) => (reduced ? { hidden: {}, show: {} } : fadeRise)
