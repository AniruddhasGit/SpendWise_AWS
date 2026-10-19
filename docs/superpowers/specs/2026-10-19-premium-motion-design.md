# Design Spec — SpendWise Premium Motion (Deliverable 1, in-site)

**Date:** 2026-10-19 · **Author:** ani87 (AniruddhaDynpro) + Claude · **Status:** approved-to-build
**Scope:** the in-site "wow" build only. The launch video (Deliverable 2, `motion-as-code`) and
true-refraction liquid glass (liquidGL) are **out of scope** here.
**Applies to:** both repos — `spendwise_render` (build here first, live on Render) then mirrored to
`spendwise_aws` (`D:/Project/SpendWise/dev`, infra currently shut down).

---

## 1. Overview & governing decision

Add **framer-motion** to the React client to make SpendWise feel premium, overriding the frozen
`SW-ADR-016` (plain CSS / no UI framework) — client-authorized 2026-10-19, recorded as **SW-ADR-156**
(§9). Plain CSS stays the default; **no Tailwind, no UI/component framework**. Glass stays CSS
`backdrop-filter`. CSP is unaffected: framer-motion is bundled and served from `'self'`
(`script-src 'self'` ok); it writes inline `transform`/`style` governed by `style-src 'unsafe-inline'`.

### 1.1 Critical finding — this is ADDITIVE, not a replacement
The existing hand-rolled motion layer (`client/src/lib/motion.js`, `client/src/styles/motion.css`)
is **carefully built around three hard invariants** and must be **kept**, not ripped out:

1. **Figure innerText invariant.** `<CountUp>` / `<Odometer>` guarantee the element's `innerText` is
   the *exact final formatted value on every frame* (ticking digits are CSS generated-content from
   data-attrs). Browser tests assert totals instantly — e.g.
   `tests/browser/test_the_website.py:123` `assert total.inner_text() == "₹1,250.00"`. A naive
   framer-motion `useSpring` count-up would animate the visible text and **break these tests + screen
   readers.** → **KEEP `<CountUp>`/`<Odometer>` as the count-up mechanism. Do NOT replace with Motion.**
2. **Glass / backdrop-filter rule.** Animating `opacity` or `filter` on a pane that contains
   `backdrop-filter` glass makes that pane the glass's *backdrop root* → the frosting breaks for the
   whole transition. `motion.css` route transitions are **transform-only** for this reason. →
   **framer-motion transitions on glass containers must be transform-only** (animate `x/y/scale`,
   never `opacity`/`filter`, on an element with frosted children). Fade only non-glass layers.
3. **Reduced motion = instant.** `tokens.css` collapses durations to `0.01ms` under
   `prefers-reduced-motion`. → wrap the app in `<MotionConfig reducedMotion="user">` so Motion obeys
   the same OS setting; keep `usePrefersReducedMotion()` / `useFinePointer()` for JS gates.

**framer-motion is therefore used only for what CSS can't do well:** the new preloader→3D card hero,
real enter/exit (`AnimatePresence`), spring gestures (`whileHover`/`whileTap`), layout animations,
and chart draw-ins. Everything the hand-rolled system already does (staggers, route-settle,
count-ups, odometers) stays.

---

## 2. Dependency & root wiring

- `client/package.json`: add `"framer-motion": "^11.x"` to `dependencies`. `npm install` locally
  (vite 5.4.11, React 18.3.1 — compatible).
- **Bundle discipline:** use `LazyMotion` + `m` (not `motion`) + `domAnimation` feature bundle
  (~18KB gz vs ~34KB). Import `m` in components; load features once at the root.
- `client/src/main.jsx`: wrap `<App/>`:
  ```jsx
  import { LazyMotion, domAnimation, MotionConfig } from 'framer-motion'
  ...
  <StrictMode>
    <LazyMotion features={domAnimation} strict>
      <MotionConfig reducedMotion="user">
        <App />
      </MotionConfig>
    </LazyMotion>
  </StrictMode>
  ```
  (`strict` forbids the heavier `motion.*` and enforces `m.*` — keeps the bundle honest.)

---

## 3. New shared layer — `client/src/lib/anim.js`

Complements `motion.js` (does NOT duplicate the figure components). Exports the Motion vocabulary so
every screen pulls one consistent feel. Contents (final):

- **Springs (transitions):** `spring` (default UI: `{type:'spring', stiffness:420, damping:34}`),
  `springSoft` (hero/large: `stiffness:120, damping:18`), `springSnappy` (tap feedback).
- **Variants:** `fadeRise` (non-glass only — opacity+y), `riseTransformOnly` (y/scale only, for
  glass panes), `staggerParent`/`staggerChild` (mirror the 40ms/cap-8 of `.sw-stagger`),
  `panelInOut` (scale+y for AnimatePresence modals), `pageInOut` (transform-only route).
- **Gesture presets:** `hoverLift = { whileHover:{y:-3, ...spring}, whileTap:{scale:0.97} }` — the
  tactile card/button feel.
- **Helper:** `reveal(reduced)` returns a no-op variant when reduced-motion is on (belt-and-braces
  on top of MotionConfig).

All values reference the existing tokens where possible (durations from `tokens.css`).

---

## 4. Centerpiece — Preloader → 3D card hero

### 4.1 The two windows (honest)
- **Window A (in-app):** HTML arrived → JS parse → fonts ready → first `/api/auth/me` resolves
  (~1-3s). Covered by the in-app splash below.
- **Window B (server cold start, 60-90s):** server asleep serves nothing; covered only by the
  **always-on static front** (§7), not the in-app splash.

### 4.2 In-app splash (index.html + React handoff)
- `client/index.html`: add a **sibling** `<div id="splash">…</div>` BEFORE `<div id="root">`, with
  an inline `<style>` block (CSS/SVG only — **no inline `<script>`**, blocked by CSP). It paints the
  instant HTML arrives: the liquid-orb + coin motif, emerald/gold, a **progress bar pinned to the
  bottom**. CSS animates an indeterminate shimmer until JS takes over.
- **Real % milestones** (no faked numbers — honesty floor): React updates the bar via a tiny
  `Splash` controller as each milestone fires — `document.readyState` → bundle executed (React
  mounted) → `document.fonts.ready` → first `api.me()` settles = 100%. Each milestone sets a width.
- Handoff: a `Splash` component (framer-motion `AnimatePresence`) **fades/scales the splash out** and
  removes `#splash` once `App`'s `checking` flips false (first data in). Drives the reveal of the
  hero/landing.

### 4.3 The 3D card hero (on the Gate landing)
- New component `client/src/components/CardRing.jsx` (framer-motion + CSS 3D). SpendWise's **own UI
  cards** — a `BankCard`, a mini chart (reuse LinePlot/Donut at small size), category tiles, an
  expense row — `m.div`s positioned on a ring via `perspective` + `rotateY(θ)` + `translateZ(r)`.
- Sequence (springSoft): cards **fly up from below → fan into an arc → close into a full ring** over
  a **clouds sky** backdrop (CSS gradient + layered cloud SVGs, emerald/gold dusk), **camera drops
  inside** (animate the ring container's `rotateX`/`z`), then it **resolves into the Gate** (the
  existing `LiquidBlob` + `BankCard` hero + sign-in/up panel). The ring is `aria-hidden` (decorative).
- Mounts in `Gate.jsx` as the hero, gated to run once per session; respects reduced-motion (instant
  to final Gate) and fine-pointer where appropriate.

---

## 5. Per-screen plan (file-by-file, parallelizable by ownership)

Each block lists **owned files** so passes don't collide. All transitions on glass = transform-only.

- **Foundation (serial, shared files):** `client/package.json`, `client/src/main.jsx`,
  `client/src/lib/anim.js`, `client/index.html`, `client/src/App.jsx` (wrap route panes in
  `AnimatePresence` with `pageInOut`, transform-only; the Gate↔shell swap gets a real exit).
- **Hero/Gate:** `client/src/screens/Gate.jsx`, `client/src/components/CardRing.jsx` (new),
  `client/src/components/Splash.jsx` (new), `client/src/styles/screens/hero.css` (new). Keep
  `TiltCard.jsx`/`LiquidBlob.jsx` (enhance with `m` springs, not replace).
- **Dashboard + charts:** `client/src/screens/Dashboard.jsx`, `components/charts/LinePlot.jsx`,
  `Bars.jsx`, `Donut.jsx`, `components/DayBars.jsx`, `components/EntryList.jsx`. Chart **draw-in** on
  mount (animate SVG path `pathLength` / bar `scaleY` with `m`), **re-tween** on period change —
  **without touching** axis/tick math or the hover-readout. List items use existing stagger +
  `hoverLift`. Totals keep `<CountUp>`/`<Odometer>`.
- **ExpensePanel + dialogs:** `components/ExpensePanel.jsx` — `AnimatePresence` spring in/out
  (`panelInOut`); it's not glass-over-glass so opacity is fine, verify.
- **Admin/Categories/Settings:** `screens/Admin.jsx`, `screens/Categories.jsx`, `screens/Settings.jsx`
  — staggered row reveals, animated tab switches, confirm-dialog `AnimatePresence` exits.
  **GUARD:** admin motion must reveal **nothing** beyond what the admin UI already shows (no amounts/
  descriptions of others except the sanctioned total/avg/line-plot — CR-001). Count-ups only on
  already-visible figures.

---

## 6. Testing / verify
- `cd client && npm run build` must succeed (no new source maps per existing vite config).
- Run the browser suite: the `total.inner_text()` assertions and the ribbon opacity cue must stay
  green (proves the invariants held). No faked progress, no admin leakage.
- Manual: 360px phone (no h-scroll), reduced-motion = instant, a cold load shows the splash→hero→Gate.

## 7. Always-on static front (spec only — build in a later pass)
A separate **static site** (unlimited-free) is the shared front door at a clean URL. It plays the
looping branded explainer + progress, and **wakes the backend by fetching `/healthz` ONLY** (no DB,
so zero Neon compute), **per real visit, never on a timer** (free-tier rule — no keep-awake cron).
When `/healthz` is healthy it hands off to the app. Level-1: clean URL is shared; raw `onrender.com`
URL is simply not shared.

## 8. Build sequence & two-repo delivery
1. Foundation (serial) in `spendwise_render` → 2. per-screen passes → 3. `npm run build` + browser
   suite green → 4. **mirror identical `client/` + index.html + the ADR to `spendwise_aws`** →
   5. commit both. **Free-tier:** batch into **ONE deploy to main per repo** (Render auto-deploys on
   push to main; builds eat free minutes) — build the image locally where feasible. Promote
   `dev→uat→main` on both; **AWS promotion waits for `infra/RESTART.md`** (uat push auto-fires CD
   against shut-down infra). Client requires both repos current to main.

## 9. SW-ADR-156 (decision)
**Title:** Permit a bundled animation library (framer-motion) for the premium client, amending
SW-ADR-016. **Status:** RULED (CLIENT, 2026-10-19). **Decision:** framer-motion is allowed in the
React client for motion that plain CSS cannot do well (3D hero, enter/exit, spring gestures, chart
draw-ins). The ban on **UI/component frameworks** (Tailwind, MUI, Chakra, etc.) stands. Plain CSS
remains the default; the existing hand-rolled figure components and invariants (§1.1) are preserved.
**Why:** client wants a premium feel; the library is bundled (CSP-safe) and additive. **Consequences:**
+~18KB gz bundle (LazyMotion); one new dependency; motion must honor the glass/innerText/reduced-motion
invariants.

## 10. Out of scope
- Deliverable 2: the kinetic launch video — built later with the `motion-as-code` skill.
- liquidGL / WebGL true-refraction glass — optional future single-accent only (mobile/perf risk).
