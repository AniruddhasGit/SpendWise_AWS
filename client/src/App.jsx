import { useCallback, useEffect, useRef, useState } from 'react'
import { api, onSessionEnded, startSession, stopSession } from './lib/api.js'
import { apply, stored, switchTheme } from './lib/theme.js'
import { carryAcross, paintScene, sceneTheme, scrollToTop, startSmoothScroll, useServerReady } from './lib/scene.js'
import Sidebar from './components/Sidebar.jsx'
import Admin from './screens/Admin.jsx'
import Categories from './screens/Categories.jsx'
import Dashboard from './screens/Dashboard.jsx'
import Gate from './screens/Gate.jsx'
import Landing from './screens/Landing.jsx'
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

// A tab that has held a session goes straight to the sign-in form when it
// reloads signed out (a revoked or expired session): that person wants the
// form, not the landing page. One bit, per tab, nothing personal in it.
// sessionStorage can throw (privacy modes), and then everyone gets the landing.
const SEEN = 'spendwise.tab-signed-in'
function tabHadSession() {
  try { return sessionStorage.getItem(SEEN) === '1' } catch { return false }
}
function markTabSignedIn() {
  try { sessionStorage.setItem(SEEN, '1') } catch { /* landing next time; harmless */ }
}

/** Drop `?from&to&category` so the next person does not inherit them. */
function clearQuery() {
  if (window.location.search) {
    window.history.replaceState(null, '', window.location.pathname + window.location.hash)
  }
}

export default function App() {
  const [principal, setPrincipal] = useState(null)
  const [checking, setChecking] = useState(true)
  const [mode, setMode] = useState('login')
  // What a signed-out visitor sees: the landing page on a first visit
  // (SW-ADR-156), the sign-in form once they ask for it. Anyone leaving the app
  // (a sign-out, an ended session, a reload after one) goes straight to the
  // form, where the reason banner and the focused email field are.
  const [front, setFront] = useState(() => (tabHadSession() ? 'gate' : 'landing'))
  const [reason, setReason] = useState(null)
  const [view, setView] = useState('dashboard')
  const [animateRoute, setAnimateRoute] = useState(false)
  const [railOpen, setRailOpen] = useState(false)
  const [theme, setTheme] = useState(stored)
  // The signed-out scene's theme: dark unless light was chosen (SW-ADR-160).
  const [scene, setScene] = useState(sceneTheme)
  // On the always-on front the server may be asleep: the landing shows its
  // tree and fog at once and counts down until the server answers.
  const { ready: serverReady, since } = useServerReady()
  const [signingOut, setSigningOut] = useState(false)
  const [gateFocus, setGateFocus] = useState(false)
  // A sign-out the server never confirmed. The session cookie is httpOnly, so
  // script cannot clear it: showing the sign-in form here would be a lie, and
  // the next person to reload would be signed in as this one.
  const [signOutError, setSignOutError] = useState(null)

  // E3-S7 AC3: a half-typed expense survives the redirect. Held HERE, above
  // the screen that gets unmounted. Memory only, never localStorage — an
  // unsaved amount is somebody's spending, and leaving it on a shared machine
  // after sign-out is a disclosure nobody asked for.
  //
  // Stored WITH ITS OWNER, `{ ownerId, form }`. A session ending keeps it on
  // purpose, and the next person to sign in at that screen may not be the one
  // who typed it: their "Add expense" must not open on someone else's amount,
  // description and (foreign) category id.
  const [draft, setDraft] = useState(null)

  const principalRef = useRef(null)
  principalRef.current = principal
  const signingOutRef = useRef(false)
  const focusMain = useRef(false)
  // The period a person was looking at when their session ended, so the SAME
  // person signing back in resumes it. Anyone else starts clean.
  const resume = useRef(null)

  /** Every piece of shell state, back to a signed-out start. One place, so a
      new piece of state cannot be reset by one exit path and missed by another. */
  const resetShell = (nextReason) => {
    setPrincipal(null)
    setMode('login')
    setFront('gate')
    setView('dashboard')
    setAnimateRoute(false)
    setRailOpen(false)
    setReason(nextReason)
    setSignOutError(null)
    setGateFocus(true)
  }

  useEffect(() => {
    onSessionEnded((err) => {
      const who = principalRef.current
      resume.current = who ? { ownerId: who.id, search: window.location.search } : null
      clearQuery()
      resetShell(err?.code === 'ACCOUNT_DEACTIVATED'
        ? err.message
        : 'Your session ended. Sign in to pick up where you left off.')
    })
  }, [])

  // Smooth scroll on every page (Lenis on GSAP's ticker).
  useEffect(() => { startSmoothScroll() }, [])

  // Signed out, the whole document wears the scene's theme, so the sign-in
  // card and its inputs match the scene around them; signed in, the person's
  // own choice (System, Light or Dark) comes back.
  useEffect(() => {
    if (principal) apply(stored())
    else paintScene(scene)
  }, [principal, scene])

  useEffect(() => {
    if (!serverReady) return undefined
    // `GET /api/auth/me` is the only way to know: the session cookie is
    // httpOnly, so script cannot see whether one exists. A 401 here is the
    // NORMAL first-visit answer, not a session ending — `me` is an auth call,
    // so it never fires the session-ended handler, and the guard is armed only
    // once a session is known to exist.
    let live = true
    api.me()
      .then((p) => { if (live) { startSession(); markTabSignedIn(); setPrincipal(p) } })
      .catch(() => { if (live) setPrincipal(null) })
      .finally(() => { if (live) setChecking(false) })
    return () => { live = false }
  }, [serverReady])

  useEffect(() => {
    // Escape closes the rail at phone width. It is an overlay there, and an
    // overlay with no keyboard dismissal is a trap.
    const onKey = (e) => { if (e.key === 'Escape') setRailOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // After a sign-in the submit button that had focus is gone with the Gate.
  // Focus the content region rather than let it fall to <body>.
  useEffect(() => {
    if (principal && focusMain.current) {
      focusMain.current = false
      document.getElementById('main')?.focus({ preventScroll: true })
    }
  }, [principal?.id])

  // A pointer press floods the page with the new theme from where it was
  // pressed (lib/theme.js); a keyboard choice switches at once.
  const chooseTheme = (next, event) => { setTheme(next); switchTheme(next, event) }
  const chooseScene = (next, event) => { setScene(next); chooseTheme(next, event) }

  const signedIn = (p) => {
    startSession()
    markTabSignedIn()
    const r = resume.current
    resume.current = null
    if (r && r.ownerId === p.id && r.search) {
      window.history.replaceState(null, '', window.location.pathname + r.search)
    } else {
      // Anyone else starts clean. Back after a sign-out can put the previous
      // person's `?from&to&category` into the URL while the Gate is showing;
      // without this the next person's dashboard would open on it, and send
      // the previous account's category id to this account's queries.
      clearQuery()
    }
    setDraft((d) => (d && d.ownerId === p.id ? d : null))
    focusMain.current = true
    // The tree is carried from the sign-in page to its place on the
    // dashboard (SW-ADR-160): the morph waits for the dashboard to draw it.
    carryAcross(() => {
      setGateFocus(false)
      setReason(null)
      setPrincipal(p)
    }, { arrive: '.dash-tree .mt-stage' })
  }

  /**
   * Idempotent: a double click, or Settings closing the account while the rail
   * button is also pressed, sends ONE logout. The epoch moves before the call,
   * so nothing still in flight from this screen can come back as a false
   * "session ended". `alreadyClosed` skips the call when the server has already
   * revoked the session and cleared the cookie (close / deactivate).
   */
  const signOut = async ({ alreadyClosed = false } = {}) => {
    if (signingOutRef.current) return
    signingOutRef.current = true
    setSigningOut(true)
    stopSession()
    if (!alreadyClosed) {
      let failed = false
      try {
        await api.logout()
      } catch (err) {
        // 401: the session was already gone, which IS signed out. Anything
        // else (offline, a timeout, a 5xx) means the server may still hold a
        // live session behind a cookie script cannot clear.
        failed = err?.status !== 401
      }
      if (failed) {
        startSession()   // the session is still live: re-arm the guard
        setRailOpen(false)
        setSignOutError('Could not sign you out. Check your connection and try again.')
        signingOutRef.current = false
        setSigningOut(false)
        return
      }
    }
    clearQuery()
    resume.current = null
    setDraft(null)
    // and back: the dashboard's tree is carried to the sign-in page
    scrollToTop()
    carryAcross(() => resetShell(null), { arrive: '.gate-tree .mt-stage' })
    signingOutRef.current = false
    setSigningOut(false)
  }

  const onDraft = useCallback(
    (form) => setDraft(form ? { ownerId: principalRef.current?.id, form } : null),
    [],
  )

  const go = (next, byPointer) => {
    // Keyboard navigation is never animated; a pointer gets the crossfade.
    setAnimateRoute(Boolean(byPointer))
    setView(next)
  }

  // The landing page is shown at once, while the session is still being
  // checked: its tree and fog need nothing from the server, and the rest of
  // it waits for `checking` to finish (see Landing).
  const landing = front === 'landing' && !principal
  const toGate = (m) => {
    setMode(m); setReason(null); setGateFocus(true)
    scrollToTop()
    carryAcross(() => setFront('gate'))
  }
  if (landing) {
    return (
      <Landing ready={!checking} since={since} theme={scene} onTheme={chooseScene}
               onSignIn={() => toGate('login')} onRegister={() => toGate('register')} />
    )
  }

  if (checking) {
    // NOT the Gate's backdrop: a signed-in person reloading would see the
    // sign-in screen flash before their dashboard. The page ground only, and
    // a wordmark that fades in after 300ms, so a fast probe shows nothing.
    return (
      <div className="boot" aria-busy="true">
        <span className="wordmark boot-mark" aria-hidden="true">SpendWise</span>
        <p className="visually-hidden" aria-live="polite">Checking your session.</p>
      </div>
    )
  }

  if (!principal) {
    return (
      <Gate mode={mode} onMode={(m) => { setMode(m); setReason(null) }} reason={reason}
            autoFocus={gateFocus} onSignedIn={signedIn} theme={scene} onTheme={chooseScene}
            onBack={() => { setReason(null); scrollToTop(); carryAcross(() => setFront('landing')) }} />
    )
  }

  // A `user` who somehow reaches the admin pane sees a refusal, not a blank —
  // and the server would refuse every request it made anyway (`E4-S1` AC3).
  const pane = view === 'admin' && principal.role !== 'admin' ? 'denied' : view

  return (
    <div className="app">
      <Sidebar view={view} onView={go} principal={principal}
               onSignOut={() => signOut()}
               signingOut={signingOut}
               open={railOpen} onClose={() => setRailOpen(false)} />

      <div className="app-main">
        <div className="topbar-mobile">
          <button type="button" className="icon-btn" data-testid="rail-open"
                  aria-label="Open menu" aria-expanded={railOpen}
                  onClick={() => setRailOpen(true)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
                 strokeLinecap="round" aria-hidden="true">
              <path d="M4 7h16M4 12h16M4 17h10" />
            </svg>
          </button>
          <span className="wordmark">SpendWise</span>
          <button type="button" className="btn-link" onClick={() => signOut()}
                  aria-disabled={signingOut ? 'true' : undefined}>
            {signingOut ? 'Signing out…' : 'Sign out'}
          </button>
        </div>

        <main id="main" className="content" tabIndex={-1}>
          {signOutError && (
            <div className="form-error shell-signout-error" role="alert"
                 data-testid="sign-out-error">
              <span>{signOutError}</span>
              <button type="button" className="btn btn-quiet btn-sm"
                      onClick={() => signOut()}
                      aria-disabled={signingOut ? 'true' : undefined}>
                {signingOut ? 'Signing out…' : 'Try again'}
              </button>
            </div>
          )}
          <div key={pane} className={animateRoute ? 'shell-pane sw-route' : 'shell-pane'}>
            {pane === 'dashboard' && (
              <Dashboard principal={principal} draft={draft?.form ?? null} onDraft={onDraft} />
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
                  section would be cosmetic. The server refuses every
                  administrative request from a normal account regardless.
                </p>
                <button type="button" className="btn" onClick={() => go('dashboard', true)}>
                  Back to your spending
                </button>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
