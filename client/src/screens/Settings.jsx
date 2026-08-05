import { useState } from 'react'
import { api } from '../lib/api.js'
import { THEMES, effective } from '../lib/theme.js'

/**
 * Settings.
 *
 * **There is no delete button, and the screen says why rather than hiding it.**
 * `SW-ADR-107` rules that user deletion does not exist in v1 — *"Deleting a
 * person's financial history is the clearest one-way door in the register"* —
 * and `spendwise_app` holds no `DELETE` on `users` at the database, so a
 * delete button would be a lie the schema itself refuses to tell.
 *
 * What is here instead (`SW-ADR-148`): **deactivate**, which is reversible, and
 * **export**, which is the counterweight. Telling someone "we keep your data"
 * while offering no way to take a copy of it is the version of this that
 * deserves the complaint.
 */
export default function Settings({ principal, theme, onTheme, onSignedOut,
                                  onPrincipal }) {
  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="entry-meta">{principal.email}</p>
        </div>
      </header>

      <Profile principal={principal} onPrincipal={onPrincipal} />
      <Appearance theme={theme} onTheme={onTheme} />
      <Password />
      <YourData />
      <Leaving onSignedOut={onSignedOut} />
    </>
  )
}

function Card({ title, description, children, tone }) {
  return (
    <section className={`card${tone ? ` card-${tone}` : ''}`}>
      <h2 className="card-heading">{title}</h2>
      {description && <p className="entry-meta card-desc">{description}</p>}
      {children}
    </section>
  )
}

function Profile({ principal, onPrincipal }) {
  const [name, setName] = useState(principal.display_name)
  const [state, setState] = useState(null)
  const [error, setError] = useState(null)

  const submit = async (event) => {
    event.preventDefault()
    setError(null)
    setState('saving')
    try {
      onPrincipal(await api.updateMe({ display_name: name.trim() }))
      setState('saved')
    } catch (err) {
      setError(err)
      setState(null)
    }
  }

  return (
    <Card title="Your name"
          description="What SpendWise calls you. Your email is your identity and cannot be changed.">
      <form className="row-form" onSubmit={submit}>
        <div className="field field-grow">
          <label htmlFor="display-name" className="visually-hidden">Display name</label>
          <input id="display-name" value={name} maxLength={100}
                 data-testid="settings-name"
                 aria-invalid={error ? 'true' : undefined}
                 onChange={(e) => { setName(e.target.value); setState(null) }} />
          {error && <span className="field-error" role="alert">{error.message}</span>}
        </div>
        <button type="submit" className="btn" data-testid="save-name"
                aria-disabled={state === 'saving' ? 'true' : undefined}>
          {state === 'saving' ? 'Saving…' : 'Save'}
        </button>
      </form>
      {state === 'saved' && (
        <p className="ok" role="status" data-testid="name-saved">Saved.</p>
      )}
    </Card>
  )
}

function Appearance({ theme, onTheme }) {
  return (
    <Card title="Appearance"
          description="System follows your device. The other two override it everywhere, on this browser.">
      <div className="segmented segmented-wide" role="radiogroup" aria-label="Theme">
        {THEMES.map((t) => (
          <button key={t} type="button" role="radio" aria-checked={theme === t}
                  className="segment" data-testid={`settings-theme-${t}`}
                  onClick={() => onTheme(t)}>
            {t === 'system' ? 'System' : t === 'light' ? 'Light' : 'Dark'}
          </button>
        ))}
      </div>
      <p className="entry-meta">
        {theme === 'system'
          ? `Currently showing ${effective(theme)}.`
          : `Always ${theme}, whatever your device is set to.`}
      </p>
    </Card>
  )
}

function Password() {
  const [form, setForm] = useState({ current_password: '', new_password: '' })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (event) => {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      const out = await api.changePassword(form)
      setForm({ current_password: '', new_password: '' })
      setResult(out)
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <Card title="Password"
          description="Changing it signs you out everywhere else and keeps you signed in here.">
      <form onSubmit={submit}>
        <div className="field">
          <label htmlFor="current-password">Current password</label>
          <input id="current-password" type="password" autoComplete="current-password"
                 value={form.current_password} onChange={set('current_password')}
                 data-testid="current-password" required />
        </div>
        <div className="field">
          <label htmlFor="new-password">New password</label>
          <input id="new-password" type="password" autoComplete="new-password"
                 value={form.new_password} onChange={set('new_password')}
                 data-testid="new-password" required
                 aria-invalid={error?.field === 'password' ? 'true' : undefined} />
          <span className="entry-meta">At least 12 characters.</span>
        </div>
        {error && (
          <p className="form-error" role="alert" data-testid="password-error">
            {error.message}
          </p>
        )}
        <button type="submit" className="btn" data-testid="change-password"
                aria-disabled={busy ? 'true' : undefined}>
          {busy ? 'Changing…' : 'Change password'}
        </button>
      </form>
      {result && (
        <p className="ok" role="status" data-testid="password-changed">
          Changed. {result.signed_out_elsewhere} other session
          {result.signed_out_elsewhere === 1 ? '' : 's'} signed out.
        </p>
      )}
    </Card>
  )
}

function YourData() {
  const [busy, setBusy] = useState(false)

  const download = async () => {
    setBusy(true)
    try {
      const data = await api.exportMine()
      // Built and revoked in the same breath. An object URL left behind pins
      // the whole export in memory for the life of the document, and this one
      // contains every amount the person has ever recorded.
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
      const a = document.createElement('a')
      a.href = url
      a.download = 'spendwise-export.json'
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Your data"
          description="Every category and every expense on this account, as JSON. Amounts are exact integers in paise.">
      <button type="button" className="btn btn-quiet" onClick={download}
              data-testid="export" aria-disabled={busy ? 'true' : undefined}>
        {busy ? 'Preparing…' : 'Download my data'}
      </button>
    </Card>
  )
}

function Leaving({ onSignedOut }) {
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState(null)

  const go = async () => {
    setError(null)
    try {
      await api.deactivate()
      onSignedOut()
    } catch (err) {
      setError(err)
    }
  }

  return (
    <Card title="Closing your account" tone="danger"
          description="Deactivating signs you out everywhere and refuses any further sign-in.">
      {/* The honest paragraph. It would be easy to write "Delete account" here
          and deactivate underneath — and a person would only find out by
          asking for their data back. */}
      <p className="card-desc">
        <strong>Your records are kept, not erased.</strong> SpendWise has no
        delete: an expense history is the one thing here that cannot be
        reconstructed, so an administrator can always restore the account
        instead of you losing it to a mis-click. Download your data first if
        you want a copy.
      </p>

      {error && (
        <p className="form-error" role="alert" data-testid="deactivate-error">
          {error.code === 'CONFLICT'
            ? 'You are the last active administrator. Promote someone else first.'
            : error.message}
        </p>
      )}

      {confirming ? (
        <div className="row-form">
          <button type="button" className="btn btn-danger" onClick={go}
                  data-testid="deactivate-confirm">
            Yes, deactivate my account
          </button>
          <button type="button" className="btn btn-quiet"
                  onClick={() => setConfirming(false)}>
            Keep it
          </button>
        </div>
      ) : (
        <button type="button" className="btn btn-danger"
                onClick={() => setConfirming(true)} data-testid="deactivate">
          Deactivate my account
        </button>
      )}
    </Card>
  )
}
