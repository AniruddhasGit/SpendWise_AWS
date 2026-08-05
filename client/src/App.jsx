import { useEffect, useState } from 'react'
import { api, armSessionGuard, onSessionEnded } from './lib/api.js'
import { apply, stored } from './lib/theme.js'
import Sidebar from './components/Sidebar.jsx'
import Admin from './screens/Admin.jsx'
import Categories from './screens/Categories.jsx'
import Dashboard from './screens/Dashboard.jsx'
import Gate from './screens/Gate.jsx'
import Settings from './screens/Settings.jsx'

/**
 * The application shell: a rail on the left, a view on the right.
 *
 * Still no router. `SRC-001 §12.1` scopes v1 to a dashboard and a sign-in; the
 * sections here are panes of one application, not addresses. The one genuinely
 * navigable state is the PERIOD, and that really is in the URL — see
 * `lib/period.js`, which owns the history entries.
 *
 * A router library would buy nothing and cost a dependency, a bundle, and a
 * second set of conventions for expressing "which pane".
 */
export default function App() {
  const [principal, setPrincipal] = useState(null)
  const [checking, setChecking] = useState(true)
  const [mode, setMode] = useState('login')
  const [reason, setReason] = useState(null)
  const [view, setView] = useState('dashboard')
  const [railOpen, setRailOpen] = useState(false)
  const [theme, setTheme] = useState(stored)

  // E3-S7 AC3: a half-typed expense survives the redirect. Held HERE, above
  // the screen that gets unmounted. Memory only, never localStorage — an
  // unsaved amount is somebody's spending, and leaving it on a shared machine
  // after sign-out is a disclosure nobody asked for.
  const [draft, setDraft] = useState(null)

  useEffect(() => {
    onSessionEnded((err) => {
      setPrincipal(null)
      setMode('login')
      setView('dashboard')
      setReason(err?.code === 'ACCOUNT_DEACTIVATED'
        ? err.message
        : 'Your session ended. Sign in to pick up where you left off.')
    })
  }, [])

  useEffect(() => {
    // `GET /api/auth/me` is the only way to know: the session cookie is
    // httpOnly, so script cannot see whether one exists. A 401 here is the
    // NORMAL first-visit answer, not a session ending — so the guard is armed
    // only once the answer is known.
    api.me()
      .then((p) => { setPrincipal(p); armSessionGuard() })
      .catch(() => setPrincipal(null))
      .finally(() => { setChecking(false); setReason(null) })
  }, [])

  useEffect(() => {
    // Escape closes the rail at phone width. It is an overlay there, and an
    // overlay with no keyboard dismissal is a trap.
    const onKey = (e) => { if (e.key === 'Escape') setRailOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const chooseTheme = (next) => { setTheme(next); apply(next) }

  const signOut = async () => {
    try { await api.logout() } catch { /* already gone is still signed out */ }
    setPrincipal(null)
    setDraft(null)
    setMode('login')
    setView('dashboard')
    setReason(null)
    armSessionGuard()
  }

  if (checking) {
    return (
      <div className="gate">
        <p className="visually-hidden" aria-live="polite">Checking your session.</p>
      </div>
    )
  }

  if (!principal) {
    return (
      <Gate mode={mode} onMode={(m) => { setMode(m); setReason(null) }} reason={reason}
            onSignedIn={(p) => { setPrincipal(p); setReason(null) }} />
    )
  }

  // A `user` who somehow reaches the admin pane sees a refusal, not a blank —
  // and the server would refuse every request it made anyway (`E4-S1` AC3).
  const pane = view === 'admin' && principal.role !== 'admin' ? 'denied' : view

  return (
    <div className="app">
      <Sidebar view={view} onView={setView} principal={principal}
               theme={theme} onTheme={chooseTheme}
               open={railOpen} onClose={() => setRailOpen(false)} />

      <div className="app-main">
        <div className="topbar-mobile">
          <button type="button" className="icon-btn" data-testid="rail-open"
                  aria-label="Open menu" aria-expanded={railOpen}
                  onClick={() => setRailOpen(true)}>☰</button>
          <span className="wordmark">SpendWise</span>
          <button type="button" className="btn-link" onClick={signOut}>Sign out</button>
        </div>

        <main id="main" className="content">
          {pane === 'dashboard' && (
            <Dashboard principal={principal} draft={draft} onDraft={setDraft} />
          )}
          {pane === 'categories' && <Categories />}
          {pane === 'settings' && (
            <Settings principal={principal} theme={theme} onTheme={chooseTheme}
                      onSignedOut={signOut} onPrincipal={setPrincipal} />
          )}
          {pane === 'admin' && <Admin principal={principal} />}
          {pane === 'denied' && (
            <div className="state" data-testid="state-denied">
              <h2 className="state-title">Not available</h2>
              <p className="state-body">
                Administration is for administrator accounts. Hiding this
                section would be cosmetic — the server refuses every
                administrative request from a normal account regardless.
              </p>
              <button type="button" className="btn" onClick={() => setView('dashboard')}>
                Back to your spending
              </button>
            </div>
          )}
        </main>

        <footer className="app-foot">
          <button type="button" className="btn-link" onClick={signOut}
                  data-testid="sign-out">Sign out</button>
        </footer>
      </div>
    </div>
  )
}
