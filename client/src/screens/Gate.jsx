import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { gsap } from 'gsap'
import { api } from '../lib/api.js'
import Fog from '../components/Fog.jsx'
import MoneyTree from '../components/MoneyTree.jsx'
import { ThemeSwitch } from '../components/SceneControls.jsx'

/**
 * Sign in and sign up. One component, because they are the same form with one
 * extra field and swapping between them must not lose what has been typed.
 *
 * `reason` is E3-S7 AC1: a session that ended mid-use lands here with a banner
 * saying so, rather than dumping the person at a bare sign-in form that looks
 * like they were never signed in.
 *
 * Layout: the hero (the money tree, quietly dropping its bills, SW-ADR-156)
 * on the left, a compact sign-in panel on the right. Stacked on a phone, with
 * the tree shrunk above the form. `onBack` returns to the landing page.
 *
 * It is the second page of the signed-out scene (SW-ADR-160): the same dusk
 * (or dawn) as the landing page, the same theme switch, and the same tree,
 * carried here by App with the fog drawn in round its base. The words arrive
 * one after another once it lands, and leave the same way on the way back.
 *
 * Session bookkeeping (epochs, arming the guard) is App's job, in
 * `onSignedIn`. This screen only asks the server and reports what it said.
 */
export default function Gate({ mode, onMode, reason, onSignedIn, onBack, autoFocus = false,
                               theme = 'dark', onTheme }) {
  const [form, setForm] = useState({ email: '', password: '', display_name: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [reveal, setReveal] = useState(false)
  const busyRef = useRef(false)
  const emailRef = useRef(null)
  const rootRef = useRef(null)
  const leaving = useRef(false)

  // The words arrive one after another while the tree settles.
  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      gsap.timeline({ defaults: { ease: 'power4.out' } })
        .from('.gate-brandrow', { y: -40, autoAlpha: 0, duration: 0.8 }, 0.25)
        .from('.gate-title', { y: 50, autoAlpha: 0, filter: 'blur(8px)', duration: 0.9 }, 0.35)
        .from('.gate-lede', { y: 24, autoAlpha: 0, duration: 0.7 }, 0.5)
        .from('.gate-card', { y: 80, autoAlpha: 0, scale: 0.96, duration: 1 }, 0.3)
        .from('.gate-card > *, .gate-card form > *', {
          y: 22, autoAlpha: 0, duration: 0.6, stagger: 0.06,
        }, 0.55)
    }, rootRef)
    return () => ctx.revert()
  }, [])

  /** Back to the landing page: the words leave first, then App carries the tree. */
  const leave = () => {
    if (leaving.current || !onBack) return
    leaving.current = true
    const q = gsap.utils.selector(rootRef)
    gsap.timeline({ onComplete: onBack })
      .to(q('.gate-card'), { y: 90, autoAlpha: 0, duration: 0.5, ease: 'power3.in' }, 0)
      .to(q('.gate-copy, .gate-brandrow'), { x: -80, autoAlpha: 0, duration: 0.45, ease: 'power3.in' }, 0)
  }

  const registering = mode === 'register'
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  // Focus lands on the email field when the person arrives from the app (a
  // sign-out or an ended session unmounted whatever had focus), and on a
  // desktop first visit. Not on a phone's first visit: that would raise the
  // keyboard over the page before anyone has read it.
  useEffect(() => {
    const fine = window.matchMedia?.('(pointer: fine)').matches
    if (autoFocus || fine) emailRef.current?.focus({ preventScroll: true })
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    // A ref, not only state: two Enter presses inside one frame both see the
    // stale `busy === false` and would send two requests.
    if (busyRef.current) return
    busyRef.current = true
    setBusy(true)
    setError(null)
    try {
      const principal = registering
        ? await api.register(form)
        : await api.login({ email: form.email, password: form.password })
      // the words leave first, then App carries the tree to the dashboard
      await new Promise((done) => {
        const q = gsap.utils.selector(rootRef)
        gsap.timeline({ onComplete: done })
          .to(q('.gate-card'), { y: -60, autoAlpha: 0, scale: 0.97, duration: 0.45, ease: 'power3.in' }, 0)
          .to(q('.gate-copy, .gate-brandrow'), { x: -80, autoAlpha: 0, duration: 0.4, ease: 'power3.in' }, 0)
      })
      onSignedIn(principal)
    } catch (err) {
      busyRef.current = false
      setError(err)
      setBusy(false)
    }
  }

  const switchMode = (e) => {
    setError(null)
    // Only a pointer gets the field's entrance; keyboard actions never animate.
    setReveal(e.detail > 0)
    onMode(registering ? 'login' : 'register')
  }

  const errorOn = (field) => (error && error.field === field ? error.message : null)

  // A wrong email or password comes back as the SAME generic 401 the server
  // sends for an expired session ("Your session has ended. Please sign in
  // again."). On a sign-in form that message is both wrong and alarming — a
  // typo is not a session ending — so a rejected credential is said plainly,
  // and said identically whether or not the email exists (no account
  // enumeration). A paused account keeps its own ACCOUNT_DEACTIVATED message.
  // App's session-ended FLOW is untouched: api.js already exempts the auth
  // calls (login / register / me) from the guard and the guard is disarmed on
  // the sign-in screen anyway, so this changes only what the form SHOWS.
  const formError =
    error && !error.field
      ? !registering && error.status === 401 && error.code !== 'ACCOUNT_DEACTIVATED'
        ? 'Wrong email or password.'
        : error.message
      : null

  return (
    <div className="gate scene" data-scene={theme} ref={rootRef}>
      <div className="gate-layout">
        <section className="gate-hero" aria-labelledby="gate-title">
          <div className="gate-brandrow">
            <span className="wordmark gate-brand">SpendWise</span>
            {onBack && (
              <button type="button" className="btn-link gate-back" data-testid="gate-back"
                      onClick={leave}>
                Back to the home page
              </button>
            )}
            {onTheme && <ThemeSwitch theme={theme} onTheme={onTheme} className="gate-theme" />}
          </div>
          <div className="gate-stage gate-tree">
            <Fog className="gate-fog gate-fog-back" layer="back" pool scene={theme} stage=".gate-tree" />
            <MoneyTree variant="gate" alwaysMove alt="" />
            <Fog className="gate-fog gate-fog-front" pool scene={theme} stage=".gate-tree" />
          </div>
          <div className="gate-copy">
            <h1 className="gate-title sw-extruded" id="gate-title">Know where every dollar goes.</h1>
            <p className="sw-lede gate-lede">
              Log a spend in seconds and see it by category and by day.
              Your figures are visible to you alone.
            </p>
          </div>
        </section>

        <section className="gate-card" aria-labelledby="gate-form-title">
          <h2 className="gate-form-title" id="gate-form-title">
            {registering ? 'Create your account' : 'Sign in'}
          </h2>
          <p className="gate-sub">
            {registering ? 'It takes a name, an email and a password.' : 'Welcome back.'}
          </p>

          {reason && (
            <p className="banner" role="status" data-testid="session-reason">{reason}</p>
          )}

          {formError && (
            <p className="form-error" role="alert" data-testid="gate-error">{formError}</p>
          )}

          <form onSubmit={submit} noValidate aria-busy={busy ? 'true' : undefined}>
            {registering && (
              <div className={reveal ? 'field gate-reveal' : 'field'}>
                <label htmlFor="display_name">Your name</label>
                <input
                  id="display_name" name="display_name" autoComplete="name"
                  value={form.display_name} onChange={set('display_name')}
                  aria-invalid={errorOn('display_name') ? 'true' : undefined}
                  aria-describedby={errorOn('display_name') ? 'display_name-error' : undefined}
                  required
                />
                {errorOn('display_name') && (
                  <span className="field-error" id="display_name-error" role="alert">
                    {errorOn('display_name')}
                  </span>
                )}
              </div>
            )}

            <div className="field">
              <label htmlFor="email">Email</label>
              <input
                ref={emailRef}
                id="email" name="email" type="email" autoComplete="email" inputMode="email"
                spellCheck={false} autoCapitalize="none"
                value={form.email} onChange={set('email')}
                aria-invalid={errorOn('email') ? 'true' : undefined}
                aria-describedby={errorOn('email') ? 'email-error' : undefined}
                required
              />
              {errorOn('email') && (
                <span className="field-error" id="email-error" role="alert">{errorOn('email')}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor="password">Password</label>
              <input
                id="password" name="password" type="password"
                autoComplete={registering ? 'new-password' : 'current-password'}
                value={form.password} onChange={set('password')}
                aria-invalid={errorOn('password') ? 'true' : undefined}
                aria-describedby={
                  [errorOn('password') && 'password-error', registering && 'password-hint']
                    .filter(Boolean).join(' ') || undefined
                }
                required
              />
              {errorOn('password') && (
                <span className="field-error" id="password-error" role="alert">
                  {errorOn('password')}
                </span>
              )}
              {registering && (
                <span className="entry-meta gate-hint" id="password-hint">At least 12 characters.</span>
              )}
            </div>

            <button
              type="submit" className="btn btn-lg btn-block gate-submit"
              data-testid="gate-submit" aria-disabled={busy ? 'true' : undefined}
            >
              {busy ? 'Just a moment…' : registering ? 'Create account' : 'Sign in'}
            </button>
          </form>

          <p className="gate-footer">
            {registering ? 'Already have an account?' : 'New to SpendWise?'}{' '}
            <button type="button" className="btn-link" data-testid="gate-switch" onClick={switchMode}>
              {registering ? 'Sign in' : 'Create one'}
            </button>
          </p>
        </section>
      </div>
    </div>
  )
}
