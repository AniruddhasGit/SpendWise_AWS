import { useState } from 'react'
import { api, armSessionGuard } from '../lib/api.js'

/**
 * Sign in and sign up. One component, because they are the same form with one
 * extra field and swapping between them must not lose what has been typed.
 *
 * `reason` is E3-S7 AC1: a session that ended mid-use lands here with a banner
 * saying so, rather than dumping the person at a bare sign-in form that looks
 * like they were never signed in.
 */
export default function Gate({ mode, onMode, reason, onSignedIn }) {
  const [form, setForm] = useState({ email: '', password: '', display_name: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const registering = mode === 'register'
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const principal = registering
        ? await api.register(form)
        : await api.login({ email: form.email, password: form.password })
      // Re-arm, so the NEXT expiry can fire its redirect. Without this a
      // person who signs back in gets no banner the second time their session
      // ends — the guard has already latched.
      armSessionGuard()
      onSignedIn(principal)
    } catch (err) {
      setError(err)
      setBusy(false)
    }
  }

  const errorOn = (field) => (error && error.field === field ? error.message : null)

  return (
    <div className="gate">
      <div className="gate-card">
        <h1 className="gate-title">SpendWise</h1>
        <p className="gate-sub">See where your money went.</p>

        {reason && (
          <p className="banner" role="status" data-testid="session-reason">{reason}</p>
        )}

        {error && !error.field && (
          <p className="form-error" role="alert" data-testid="gate-error">{error.message}</p>
        )}

        <form onSubmit={submit} noValidate>
          {registering && (
            <div className="field">
              <label htmlFor="display_name">Your name</label>
              <input
                id="display_name" name="display_name" autoComplete="name"
                value={form.display_name} onChange={set('display_name')}
                aria-invalid={errorOn('display_name') ? 'true' : undefined} required
              />
              {errorOn('display_name') && (
                <span className="field-error" role="alert">{errorOn('display_name')}</span>
              )}
            </div>
          )}

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email" name="email" type="email" autoComplete="email"
              value={form.email} onChange={set('email')}
              aria-invalid={errorOn('email') ? 'true' : undefined} required
            />
            {errorOn('email') && (
              <span className="field-error" role="alert">{errorOn('email')}</span>
            )}
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password" name="password" type="password"
              autoComplete={registering ? 'new-password' : 'current-password'}
              value={form.password} onChange={set('password')}
              aria-invalid={errorOn('password') ? 'true' : undefined} required
            />
            {errorOn('password') && (
              <span className="field-error" role="alert">{errorOn('password')}</span>
            )}
            {registering && (
              <span className="entry-meta">At least 12 characters.</span>
            )}
          </div>

          <button
            type="submit" className="btn" style={{ width: '100%' }}
            data-testid="gate-submit" aria-disabled={busy ? 'true' : undefined}
          >
            {busy ? 'Just a moment…' : registering ? 'Create account' : 'Sign in'}
          </button>
        </form>

        <p className="gate-footer">
          {registering ? 'Already have an account?' : 'New to SpendWise?'}{' '}
          <button
            type="button" className="btn-link" data-testid="gate-switch"
            onClick={() => { setError(null); onMode(registering ? 'login' : 'register') }}
          >
            {registering ? 'Sign in' : 'Create one'}
          </button>
        </p>
      </div>
    </div>
  )
}
