import { effective, THEMES } from '../lib/theme.js'

/**
 * The left rail. Navigation, appearance, and the way out.
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
const ICONS = {
  dashboard: '◧',
  categories: '◔',
  settings: '⚙',
  admin: '⚿',
}

export default function Sidebar({ view, onView, principal, theme, onTheme,
                                 open, onClose }) {
  const items = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'categories', label: 'Categories' },
    { id: 'settings', label: 'Settings' },
  ]
  if (principal.role === 'admin') items.push({ id: 'admin', label: 'Administration' })

  return (
    <>
      {/* At phone width the rail slides over the content, so it needs a scrim
          to close on — and the scrim is `aria-hidden` because the close
          affordance a keyboard user needs is Escape and the rail's own button,
          not a div. */}
      {open && <div className="rail-scrim" aria-hidden="true" onClick={onClose} />}

      <nav className={`rail${open ? ' is-open' : ''}`} aria-label="Sections"
           data-testid="sidebar">
        <div className="rail-brand">
          <span className="wordmark">SpendWise</span>
          <button type="button" className="icon-btn rail-close" onClick={onClose}
                  aria-label="Close menu" data-testid="rail-close">✕</button>
        </div>

        <ul className="rail-nav">
          {items.map((it) => (
            <li key={it.id}>
              <button
                type="button"
                className="rail-item"
                data-testid={`nav-${it.id}`}
                aria-current={view === it.id ? 'page' : undefined}
                onClick={() => { onView(it.id); onClose() }}
              >
                <span className="rail-icon" aria-hidden="true">{ICONS[it.id]}</span>
                {it.label}
              </button>
            </li>
          ))}
        </ul>

        <div className="rail-section">
          <h2 className="rail-heading" id="appearance-label">Appearance</h2>
          {/* A radiogroup, not three toggles. The three states are mutually
              exclusive and "System" is the absence of an override rather than
              a third colour — `aria-pressed` on three buttons would say they
              can all be off, which they cannot. */}
          <div className="segmented" role="radiogroup" aria-labelledby="appearance-label">
            {THEMES.map((t) => (
              <button
                key={t}
                type="button"
                role="radio"
                aria-checked={theme === t}
                className="segment"
                data-testid={`theme-${t}`}
                onClick={() => onTheme(t)}
              >
                {t === 'system' ? 'System' : t === 'light' ? 'Light' : 'Dark'}
              </button>
            ))}
          </div>
          <p className="rail-hint" data-testid="theme-effective">
            {theme === 'system'
              ? `Following your device — currently ${effective(theme)}.`
              : `Always ${theme}.`}
          </p>
        </div>

        <div className="rail-foot">
          <span className="rail-who" data-testid="whoami">{principal.display_name}</span>
          <span className="entry-meta">{principal.email}</span>
          {principal.role === 'admin' && (
            <span className="pill" data-testid="role-pill">administrator</span>
          )}
        </div>
      </nav>
    </>
  )
}
