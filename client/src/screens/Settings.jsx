import { useState } from 'react'
import { api } from '../lib/api.js'
import { THEMES, effective } from '../lib/theme.js'
import { BankCard } from '../components/TiltCard.jsx'

/**
 * Settings.
 *
 * **There are now two ways out, and the screen says exactly what each one
 * does.** `SW-ADR-107` ruled that user deletion did not exist in v1 —
 * *"Deleting a person's financial history is the clearest one-way door in the
 * register"* — and its own text said deletion would arrive as a superseding
 * ADR. `CR-001` is that arrival, and it names the form: **soft**. `SW-ADR-150`
 * implements it as `deleted_at`, which is the version that does not walk
 * through the one-way door — nothing is erased, so nothing is unrecoverable.
 *
 * So the choice below is genuinely a choice and not two labels on one action:
 * **deactivate** is "pause me", **delete** is "close it", and the copy on each
 * says which. Alongside them sits **export** (`SW-ADR-148`), the counterweight:
 * telling someone "we keep your records" while offering no way to take a copy
 * is the version of this that deserves the complaint. It is offered again, in
 * the confirm step, because that is the last moment it is any use to them.
 */
export default function Settings({ principal, theme, onTheme, onSignedOut,
                                  onPrincipal }) {
  // The draft name lives HERE, one level above the form, so the card in the
  // header can show it as it is typed. The card is a preview and nothing more:
  // it is aria-hidden, and the saved name still comes back from the server.
  const [name, setName] = useState(principal.display_name)

  return (
    <div className="settings">
      <header className="page-head settings-head">
        <div className="settings-head-text">
          <p className="sw-eyebrow">Your account</p>
          <h1 className="page-title">Settings</h1>
          <p className="entry-meta">{principal.email}</p>
        </div>
        <div className="sw-stage settings-card">
          <span className="sw-rosette" aria-hidden="true" />
          <BankCard decorative
                    holder={name.trim() || principal.display_name}
                    meta={principal.role === 'admin' ? 'Administrator' : 'Member'}
                    last4={String(principal.id).padStart(4, '0').slice(-4)} />
        </div>
      </header>

      <div className="settings-sections sw-stagger">
        <Profile onPrincipal={onPrincipal} name={name} setName={setName} />
        <Appearance theme={theme} onTheme={onTheme} />
        <Password />
        <YourData />
        <Leaving principal={principal} onSignedOut={onSignedOut} />
      </div>
    </div>
  )
}

/**
 * One settings section: heading and explanation on the left, the controls on
 * the right, stacked below 900px. The split is also the reading order, so
 * nothing moves for a screen reader when the columns collapse.
 */
function Card({ title, description, children, tone }) {
  return (
    <section className={`card settings-section${tone ? ` card-${tone}` : ''}`}>
      <div className="settings-section-head">
        <h2 className="card-heading">{title}</h2>
        {description && <p className="entry-meta card-desc">{description}</p>}
      </div>
      <div className="settings-section-body">{children}</div>
    </section>
  )
}

function Profile({ onPrincipal, name, setName }) {
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
        <p className="ok sw-pop" role="status" data-testid="name-saved">Saved.</p>
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
      <form className="settings-password" onSubmit={submit}>
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
          <span className="entry-meta field-hint">At least 12 characters.</span>
        </div>
        {error && (
          <p className="form-error sw-pop" role="alert" data-testid="password-error">
            {error.message}
          </p>
        )}
        <button type="submit" className="btn" data-testid="change-password"
                aria-disabled={busy ? 'true' : undefined}>
          {busy ? 'Changing…' : 'Change password'}
        </button>
      </form>
      {result && (
        <p className="ok sw-pop" role="status" data-testid="password-changed">
          Changed. {result.signed_out_elsewhere} other session
          {result.signed_out_elsewhere === 1 ? '' : 's'} signed out.
        </p>
      )}
    </Card>
  )
}

/**
 * The export, hoisted out of its card because TWO places need it: the "Your
 * data" card offers it on its own terms, and the delete confirm offers it as
 * the last thing before a door closes (`CR-001 §3`: "Offer the export first").
 * Written twice it would be two chances to forget the `revokeObjectURL`, and
 * the copy that forgot would be the one on the path where the person is about
 * to lose access to the data anyway.
 */
async function downloadMyData() {
  const data = await api.exportMine()
  // Built and revoked in the same breath. An object URL left behind pins the
  // whole export in memory for the life of the document, and this one contains
  // every amount the person has ever recorded.
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
  const a = document.createElement('a')
  a.href = url
  a.download = 'spendwise-export.json'
  a.click()
  URL.revokeObjectURL(url)
}

function YourData() {
  const [busy, setBusy] = useState(false)

  const download = async () => {
    setBusy(true)
    try {
      await downloadMyData()
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card title="Your data"
          description="Every category and every expense on this account, as JSON. Amounts are exact integers in paise.">
      <div className="settings-export">
        <button type="button" className="btn btn-quiet" onClick={download}
                data-testid="export" aria-disabled={busy ? 'true' : undefined}>
          {busy ? 'Preparing…' : 'Download my data'}
        </button>
        <span className="entry-meta">spendwise-export.json</span>
      </div>
    </Card>
  )
}

/**
 * The two ways out, in one card, each with its own two-step confirm.
 *
 * They are laid out SIDE BY SIDE and not as a primary action with a hidden
 * alternative, because the whole risk `CR-001` reintroduces is a person
 * choosing the wrong one: "deactivate" and "delete" both mean "I am done" in
 * ordinary English, and only the copy distinguishes them. A person who reads
 * neither should still land somewhere reversible, which both of these are.
 */
function Leaving({ principal, onSignedOut }) {
  // `null | 'deactivate' | 'delete'` — one at a time, so opening the second
  // confirm closes the first. Two independent booleans would let both confirm
  // blocks sit open at once with two red buttons a thumb apart.
  const [confirming, setConfirming] = useState(null)
  // The failing ACTION is kept with the error, so the message renders under the
  // control that produced it. A shared error slot puts "you are the last
  // administrator" under whichever button was clicked last.
  const [failed, setFailed] = useState(null)

  const go = (which, call) => async () => {
    setFailed(null)
    try {
      await call()
      // Both endpoints have already cleared the cookie and revoked the
      // sessions by this point; `onSignedOut` is what resets the CLIENT — the
      // in-memory draft, the pane, the sign-in reason — so the next screen is
      // the gate and not a dashboard firing 401s.
      onSignedOut()
    } catch (err) {
      setFailed({ which, err })
    }
  }

  const errorFor = (which) => (failed && failed.which === which ? failed.err : null)

  return (
    <Card title="Closing your account" tone="danger"
          description="Two ways out, and they are not the same. One pauses the account; the other closes it. Neither erases anything.">
      {/* The honest paragraph, and it survives `CR-001` unchanged in substance:
          deletion arrived as a SOFT delete (`SW-ADR-150`), so "kept, not
          erased" is still the true sentence. It would be easy to relabel the
          old button and change nothing underneath — and a person would only
          find out by asking for their data back. */}
      <p className="card-desc leaving-note">
        <strong>Your records are kept, not erased.</strong> An expense history
        is the one thing here that cannot be reconstructed, so neither of these
        throws any of it away and an administrator can undo either one. Take a
        copy first if you want one: <em>Your data</em>, just above.
      </p>

      <div className="leaving">
        <section className="leaving-option">
          <h3 className="leaving-title">Pause it</h3>
          <p className="entry-meta">
            Signs you out everywhere and refuses any further sign-in. Your
            email address stays yours, and an administrator can switch it back
            on whenever you ask.
          </p>

          {errorFor('deactivate') && (
            <p className="form-error sw-pop" role="alert" data-testid="deactivate-error">
              {errorFor('deactivate').code === 'CONFLICT'
                ? 'You are the last active administrator. Promote someone else first.'
                : errorFor('deactivate').message}
            </p>
          )}

          {confirming === 'deactivate' ? (
            <div className="row-form leaving-confirm sw-enter">
              <button type="button" className="btn btn-danger"
                      onClick={go('deactivate', api.deactivate)}
                      data-testid="deactivate-confirm">
                Yes, deactivate my account
              </button>
              <button type="button" className="btn btn-quiet"
                      onClick={() => setConfirming(null)}>
                Keep it
              </button>
            </div>
          ) : (
            <button type="button" className="btn btn-danger-quiet"
                    onClick={() => { setFailed(null); setConfirming('deactivate') }}
                    data-testid="deactivate">
              Deactivate my account
            </button>
          )}
        </section>

        <section className="leaving-option">
          <h3 className="leaving-title">Close it</h3>
          <p className="entry-meta">
            Marks the account closed and ends it. Reversible by an
            administrator, and your records stay where they are.
          </p>

          {errorFor('delete') && (
            <p className="form-error sw-pop" role="alert" data-testid="delete-account-error">
              {/* 409 with `field: "is_active"` (`CR-001 §2`). The generic
                  message would be "Conflict", which tells a person nothing
                  about what to do — and what to do is specific and doable. */}
              {errorFor('delete').code === 'CONFLICT'
                ? 'You are the last active administrator, so this account cannot be '
                  + 'closed: there would be nobody left who can restore accounts or '
                  + 'promote anyone. Promote another administrator first, then come back.'
                : errorFor('delete').message}
            </p>
          )}

          {confirming === 'delete' ? (
            <DeleteConfirm principal={principal}
                           onGo={go('delete', api.deleteMe)}
                           onCancel={() => setConfirming(null)} />
          ) : (
            <button type="button" className="btn btn-danger-quiet"
                    onClick={() => { setFailed(null); setConfirming('delete') }}
                    data-testid="delete-account">
              Delete my account
            </button>
          )}
        </section>
      </div>
    </Card>
  )
}

/**
 * Step two of the close. Four sentences, and every one of them is something a
 * person is entitled to know BEFORE the button rather than after it.
 *
 * `CR-001` is explicit that the copy has to be specific, and each line below is
 * a real consequence of the implementation and not reassurance: sign-in is
 * refused with the same generic 401 as a wrong password (`SW-ADR-100 (1)`),
 * every row survives, `POST /api/admin/users/{id}/active` with `is_active:
 * true` clears `deleted_at` in one action, and the unique index on
 * `lower(email)` stays TOTAL — which is the consequence nobody expects and the
 * one they will discover at the worst moment, trying to sign up again.
 */
function DeleteConfirm({ principal, onGo, onCancel }) {
  const [exporting, setExporting] = useState(false)

  const exportFirst = async () => {
    setExporting(true)
    try {
      await downloadMyData()
    } finally {
      setExporting(false)
    }
  }

  return (
    <div className="leaving-confirm sw-enter" data-testid="delete-account-confirmation">
      <ul className="consequences">
        <li>
          The account closes, and signing in is refused from that moment,
          with the same answer a wrong password gets, so the sign-in screen
          never reveals that it happened.
        </li>
        <li>
          <strong>Every expense and category is kept.</strong> Nothing is
          deleted from the database; the account is marked closed.
        </li>
        <li>
          An administrator can restore it, in one action, with everything
          still attached.
        </li>
        <li>
          <strong>{principal.email} stays taken.</strong> That address cannot
          be used to register a new account while this one exists. Ask an
          administrator to restore this account instead of making another.
        </li>
      </ul>

      <div className="row-form leaving-actions">
        {/* The export, offered at the last useful moment. It is the same
            function the card above calls, so there is no second version of it
            to drift. */}
        <button type="button" className="btn btn-quiet" onClick={exportFirst}
                data-testid="delete-account-export"
                aria-disabled={exporting ? 'true' : undefined}>
          {exporting ? 'Preparing…' : 'Download my data first'}
        </button>
        <button type="button" className="btn btn-danger" onClick={onGo}
                data-testid="delete-account-confirm">
          Yes, close my account
        </button>
        <button type="button" className="btn btn-quiet" onClick={onCancel}>
          Keep it
        </button>
      </div>
    </div>
  )
}
