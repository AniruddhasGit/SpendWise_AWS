import { useEffect, useState } from 'react'
import { api, armSessionGuard, onSessionEnded } from './lib/api.js'
import Dashboard from './screens/Dashboard.jsx'
import Gate from './screens/Gate.jsx'

/**
 * The whole application, which is two screens and the thing that decides
 * between them.
 *
 * There is no router. `SRC-001 §12.1` scopes v1 to one dashboard and a sign-in
 * — a router library would be a dependency, a bundle and a set of conventions
 * bought to express one boolean. The PERIOD is in the URL and handled by
 * `period.js`; that is the only navigable state there is.
 */
export default function App() {
  const [principal, setPrincipal] = useState(null)
  const [checking, setChecking] = useState(true)
  const [mode, setMode] = useState('login')
  const [reason, setReason] = useState(null)

  // E3-S7 AC3: a half-typed expense survives the redirect. Held HERE, above
  // the screen that gets unmounted — inside the dashboard it would be
  // destroyed by the very navigation it needs to survive. Memory only, never
  // localStorage: an unsaved amount is somebody's spending, and leaving it on
  // a shared machine after sign-out is a disclosure nobody asked for.
  const [draft, setDraft] = useState(null)

  useEffect(() => {
    onSessionEnded((err) => {
      setPrincipal(null)
      setMode('login')
      setReason(err?.code === 'ACCOUNT_DEACTIVATED'
        ? err.message
        : 'Your session ended. Sign in to pick up where you left off.')
    })
  }, [])

  useEffect(() => {
    // `GET /api/auth/me` is the only way to know: the session cookie is
    // httpOnly, so script cannot see whether one exists. A 401 here is the
    // NORMAL first-visit answer, not a session ending — so the guard is armed
    // only after we know the answer.
    api.me()
      .then((p) => { setPrincipal(p); armSessionGuard() })
      .catch(() => { setPrincipal(null) })
      .finally(() => { setChecking(false); setReason(null) })
  }, [])

  const signOut = async () => {
    try { await api.logout() } catch { /* already gone is still signed out */ }
    setPrincipal(null)
    setDraft(null)
    setMode('login')
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
      <Gate
        mode={mode}
        onMode={(m) => { setMode(m); setReason(null) }}
        reason={reason}
        onSignedIn={(p) => { setPrincipal(p); setReason(null) }}
      />
    )
  }

  return (
    <Dashboard
      principal={principal}
      draft={draft}
      onDraft={setDraft}
      onSignOut={signOut}
    />
  )
}
