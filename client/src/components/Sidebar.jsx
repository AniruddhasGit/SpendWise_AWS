import { useEffect, useRef, useState } from 'react'

const NARROW = '(max-width: 900px)'

/** True at phone width, where the rail is an off-canvas overlay. */
function useNarrow() {
  const [narrow, setNarrow] = useState(() => window.matchMedia?.(NARROW).matches ?? false)
  useEffect(() => {
    const mq = window.matchMedia?.(NARROW)
    if (!mq) return undefined
    const on = () => setNarrow(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return narrow
}

/**
 * The left rail. Navigation and the way out.
 *
 * A `<nav>` with a list of real `<button>`s, not links: there is no router
 * (`SRC-001 §12.1` scopes v1 to a dashboard and a sign-in), so an `<a href>`
 * would be a lie about what clicking does — and a lie a screen reader repeats.
 * The one navigable state this product has is the PERIOD, and that genuinely
 * is in the URL.
 *
 * **The admin item appears only for an admin, and that is cosmetic.**
 * `SRC-001 §9.1` says so in the client's own words: *"Hiding the admin link in
 * the UI is cosmetic, the real check is `require_admin` on the server for
 * every request."* This component is the cosmetic half; `app/core/deps.py` is
 * the real one.
 */
// Hand-drawn, 24 viewBox, 1.75 stroke, currentColor (DESIGN-SYSTEM.md §9.10).
// No icon library: the stack is locked (SW-ADR-016).
const ICON_PATHS = {
  // a statement: a card with a rising line
  dashboard: 'M4 5.5h16v13H4zM7.5 15l3-3.5 2.5 2 3.5-4.5',
  // a stack of coins
  categories: 'M5 7c0-1.4 3.1-2.5 7-2.5s7 1.1 7 2.5-3.1 2.5-7 2.5S5 8.4 5 7zM5 7v5c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V7M5 12v5c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5v-5',
  // sliders
  settings: 'M5 8h9M18 8h1M5 16h1M10 16h9M16 6v4M8 14v4',
  // a shield
  admin: 'M12 3.5 19 6v5.5c0 4.2-3 7.4-7 9-4-1.6-7-4.8-7-9V6z',
}

function Icon({ name }) {
  return (
    <svg className="rail-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={ICON_PATHS[name]} />
    </svg>
  )
}

export default function Sidebar({ view, onView, principal,
                                 open, onClose, onSignOut, signingOut = false }) {
  const items = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'categories', label: 'Categories' },
    { id: 'settings', label: 'Settings' },
  ]
  if (principal.role === 'admin') items.push({ id: 'admin', label: 'Administration' })

  const narrow = useNarrow()
  const closeRef = useRef(null)
  const returnTo = useRef(null)
  // At phone width a closed rail is off screen, and off screen is not the
  // same as unreachable: without `inert` its buttons stay in the Tab order,
  // and focus walks into a panel nobody can see.
  const hidden = narrow && !open

  // At phone width the open rail is a MODAL overlay: it covers the content,
  // so the content must be unreachable while it is open (WCAG 2.4.3, 2.4.11).
  // Without this, Tab walks out of the rail into buttons hidden under it.
  // Declared BEFORE the focus effect: React runs every cleanup before any
  // setup, so `inert` is already gone when focus is handed back to the opener
  // (which lives in .app-main) — focus() on an inert node is a silent no-op.
  useEffect(() => {
    if (!(narrow && open)) return undefined
    // The skip link (index.html) sits outside the app and points into the
    // content, so it goes inert with it.
    const covered = [document.querySelector('.app-main'), document.querySelector('.skip-link')]
      .filter(Boolean)
    for (const el of covered) el.inert = true
    return () => { for (const el of covered) el.inert = false }
  }, [narrow, open])

  // Opening moves focus into the rail; closing ALWAYS hands it back to the
  // button that opened it. With the content inert, focus can only have been
  // in the rail (or on <body>), so there is nowhere better for it to go.
  useEffect(() => {
    if (!narrow) return
    if (open) {
      returnTo.current = document.activeElement
      closeRef.current?.focus({ preventScroll: true })
    } else if (returnTo.current) {
      const opener = document.querySelector('[data-testid="rail-open"]')
      const back = opener || returnTo.current
      returnTo.current = null
      back.focus?.({ preventScroll: true })
    }
  }, [open, narrow])

  return (
    <>
      {/* At phone width the rail slides over the content, so it needs a scrim
          to close on — and the scrim is `aria-hidden` because the close
          affordance a keyboard user needs is Escape and the rail's own button,
          not a div. */}
      {open && <div className="rail-scrim" aria-hidden="true" onClick={onClose} />}

      <nav className={`rail${open ? ' is-open' : ''}`} aria-label="Sections" data-lenis-prevent=""
           data-testid="sidebar" inert={hidden ? '' : undefined}>
        <div className="rail-brand sw-focus">
          <span className="wordmark">SpendWise</span>
          <button type="button" className="icon-btn rail-close" onClick={onClose} ref={closeRef}
                  aria-label="Close menu" data-testid="rail-close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
                 strokeLinecap="round" aria-hidden="true">
              <path d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        </div>

        <ul className="rail-nav">
          {items.map((it, i) => (
            <li key={it.id} className="sw-focus" style={{ '--sw-i': i + 1 }}>
              <button
                type="button"
                className="rail-item"
                data-testid={`nav-${it.id}`}
                aria-current={view === it.id ? 'page' : undefined}
                // `detail` is 0 for a keyboard activation: only a pointer
                // gets the route crossfade.
                onClick={(e) => { onView(it.id, e.detail > 0); onClose() }}
              >
                <Icon name={it.id} />
                <span>{it.label}</span>
              </button>
            </li>
          ))}
        </ul>

        {/* Appearance lives in Settings only (owner, 2026-10-20). */}

        {/* Sign out lives HERE, beside the account it signs out of. It used to
            sit alone in a page footer, which is the one place a person does not
            look for it — they look at their own name. Moving it rather than
            adding a second control keeps `data-testid="sign-out"` unique, which
            two browser tests rely on. */}
        <div className="rail-foot">
          <div className="rail-account">
            <span className="rail-avatar" aria-hidden="true">
              {(principal.display_name || principal.email || '?').trim().charAt(0).toUpperCase()}
            </span>
            <span className="rail-id">
              <span className="rail-who" data-testid="whoami">{principal.display_name}</span>
              <span className="entry-meta rail-email">{principal.email}</span>
            </span>
          </div>
          {principal.role === 'admin' && (
            <span className="pill pill-gold" data-testid="role-pill">administrator</span>
          )}
          <button type="button" className="btn btn-quiet btn-sm rail-signout"
                  onClick={onSignOut} data-testid="sign-out"
                  aria-disabled={signingOut ? 'true' : undefined}>
            {signingOut ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </nav>
    </>
  )
}
