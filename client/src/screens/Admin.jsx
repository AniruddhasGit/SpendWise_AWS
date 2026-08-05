import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api.js'
import { longDate, shortDate } from '../lib/money.js'
import Bars from '../components/charts/Bars.jsx'
import LinePlot from '../components/charts/LinePlot.jsx'

/**
 * Administration.
 *
 * **There is no money on this screen, and there is no way to put any there.**
 * `SRC-001 §4.2`, the client's own permission matrix:
 *
 *     | See anyone else's expense amounts | user: no | admin: **no** |
 *
 * The bold **no** is theirs. Every figure below counts accounts, sessions,
 * actions or rows. The only route from an admin to another person's expenses
 * is `admin_expense_stats()`, a `SECURITY DEFINER` function whose return type
 * declares two columns — a count and a date — so "how much" is unanswerable at
 * the database, not merely absent from a response model (`SW-ADR-129`,
 * `SW-ADR-149`).
 *
 * So this is an operations console, not a finance one: who exists, who is
 * active, who is signed in, and what administrators have done.
 */
const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'accounts', label: 'Accounts' },
  { id: 'sessions', label: 'Signed in now' },
  { id: 'audit', label: 'Audit log' },
]

export default function Admin({ principal }) {
  const [tab, setTab] = useState('overview')

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Administration</h1>
          <p className="entry-meta">
            Accounts and activity. No screen here can show another person's
            amounts — that is enforced by the database, not by this page.
          </p>
        </div>
      </header>

      <div className="tabs" role="tablist" aria-label="Administration sections">
        {TABS.map((t) => (
          <button key={t.id} type="button" role="tab" className="tab"
                  aria-selected={tab === t.id} data-testid={`admin-tab-${t.id}`}
                  onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <Overview />}
      {tab === 'accounts' && <Accounts me={principal} />}
      {tab === 'sessions' && <Sessions />}
      {tab === 'audit' && <Audit />}
    </>
  )
}

function useAsync(fn, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const run = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      setState({ data: await fn(), error: null, loading: false })
    } catch (err) {
      if (err.status !== 401) setState({ data: null, error: err, loading: false })
    }
  }, deps)                                            // eslint-disable-line
  useEffect(() => { run() }, [run])
  return [state, run]
}

// ── overview ───────────────────────────────────────────────────────────────
function Overview() {
  const [{ data, error, loading }] = useAsync(() => api.adminOverview(), [])

  if (error) return <p className="form-error" role="alert">{error.message}</p>
  if (loading || !data) return <p className="entry-meta" aria-live="polite">Loading…</p>

  const count = (n) => String(n)

  return (
    <>
      <section className="cards" aria-label="Totals" data-testid="admin-overview">
        <Stat label="Accounts" value={data.accounts_total} testId="stat-accounts"
              hint={`${data.admins} administrator${data.admins === 1 ? '' : 's'}`} />
        <Stat label="Active" value={data.accounts_active} testId="stat-active"
              hint={`${data.accounts_deactivated} deactivated`} />
        <Stat label="Signed in now" value={data.sessions_live} testId="stat-sessions"
              hint="live sessions across all accounts" />
        <Stat label="Expenses recorded" value={data.expenses_recorded}
              testId="stat-expenses" hint="a count of rows — never a sum" />
      </section>

      <section className="panels" aria-label="Activity">
        <article className="card">
          <h2 className="card-heading">New accounts, last 30 days</h2>
          {/* The one honest time series an admin can plot: it comes from
              `users.created_at`, which is nobody's money. The plot takes
              `total_paise`-shaped rows, so the counts are passed in that slot
              and formatted as counts — the component never assumes currency. */}
          <LinePlot
            days={data.signups.map((d) => ({ date: d.date, total_paise: d.count }))}
            height={140} format={count} noun="signups" />
          <p className="entry-meta" data-testid="signups-total">
            {data.signups.reduce((n, d) => n + d.count, 0)} in the last 30 days.
          </p>
        </article>

        <article className="card">
          <h2 className="card-heading">How accounts are being used</h2>
          <Bars
            testId="usage-bars"
            label="Accounts by recency of activity"
            format={count}
            rows={[
              { label: 'Active this week', value: data.accounts_active_last_7_days },
              { label: 'Dormant 30d+', value: data.accounts_dormant_30_days },
              { label: 'Never used', value: data.accounts_never_used },
            ]} />
          <p className="entry-meta">
            Recency comes from each account's most recent expense DATE. The
            amounts behind those dates are not readable from here.
          </p>
        </article>
      </section>
    </>
  )
}

function Stat({ label, value, hint, testId }) {
  return (
    <article className="card">
      <p className="card-label">{label}</p>
      <p className="card-value sw-num" data-testid={testId}>{value}</p>
      {hint && <p className="entry-meta">{hint}</p>}
    </article>
  )
}

// ── accounts ───────────────────────────────────────────────────────────────
function Accounts({ me }) {
  const [q, setQ] = useState('')
  const [notice, setNotice] = useState(null)
  const [error, setError] = useState(null)
  const [{ data, loading }, reload] = useAsync(
    () => api.adminUsers({ q: q || undefined, limit: 100 }), [q])

  const act = async (label, fn) => {
    setError(null)
    setNotice(null)
    try {
      const out = await fn()
      setNotice(typeof out === 'object' && out?.token
        ? `Reset code for that account — copy it now, it is shown once: ${out.token}`
        : label)
      await reload()
    } catch (err) {
      setError(err)
    }
  }

  return (
    <>
      <div className="row-form">
        <div className="field field-grow">
          <label htmlFor="admin-search" className="visually-hidden">Search accounts</label>
          <input id="admin-search" placeholder="Search by email or name"
                 data-testid="admin-search" value={q}
                 onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      {error && (
        <p className="form-error" role="alert" data-testid="admin-error">
          {error.code === 'CONFLICT'
            ? 'That would leave no active administrator.'
            : error.code === 'FORBIDDEN'
            ? 'An administrator cannot reset another administrator. Demote them first.'
            : error.message}
        </p>
      )}
      {notice && (
        <p className="ok notice" role="status" data-testid="admin-notice">{notice}</p>
      )}

      {loading && !data ? <p className="entry-meta">Loading…</p> : (
        <div className="table-wrap">
          <table className="table" data-testid="admin-users">
            <thead>
              <tr>
                <th scope="col">Account</th>
                <th scope="col">Role</th>
                <th scope="col">Status</th>
                <th scope="col" className="num">Expenses</th>
                <th scope="col">Last activity</th>
                <th scope="col"><span className="visually-hidden">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((u) => (
                <tr key={u.id} data-testid={`admin-user-${u.id}`}>
                  <td>
                    <span className="cell-strong">{u.display_name}</span>
                    <span className="entry-meta cell-sub">{u.email}</span>
                  </td>
                  <td>
                    {u.role === 'admin'
                      ? <span className="pill">admin</span>
                      : <span className="entry-meta">user</span>}
                  </td>
                  <td>
                    <span className={u.is_active ? 'ok-dot' : 'off-dot'} aria-hidden="true" />
                    {u.is_active ? 'active' : 'deactivated'}
                  </td>
                  {/* A COUNT. There is no column here that could hold a sum,
                      and no endpoint that could fill one. */}
                  <td className="num sw-num">{u.expense_count}</td>
                  <td className="entry-meta">
                    {u.last_activity ? shortDate(u.last_activity) : 'never'}
                  </td>
                  <td className="row-actions">
                    <button type="button" className="icon-btn"
                            data-testid={`revoke-${u.id}`}
                            onClick={() => act('Signed out.', () => api.adminRevoke(u.id))}>
                      Sign out
                    </button>
                    <button type="button" className="icon-btn"
                            data-testid={`toggle-active-${u.id}`}
                            onClick={() => act(
                              u.is_active ? 'Deactivated.' : 'Reactivated.',
                              () => api.adminSetActive(u.id, !u.is_active))}>
                      {u.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                    <button type="button" className="icon-btn"
                            data-testid={`toggle-role-${u.id}`}
                            onClick={() => act('Role changed.',
                              () => api.adminSetRole(u.id, u.role === 'admin' ? 'user' : 'admin'))}>
                      {u.role === 'admin' ? 'Demote' : 'Promote'}
                    </button>
                    <button type="button" className="icon-btn"
                            data-testid={`reset-${u.id}`}
                            onClick={() => act(null, () => api.adminReset(u.id))}>
                      Reset password
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

// ── sessions ───────────────────────────────────────────────────────────────
function Sessions() {
  const [{ data, error, loading }] = useAsync(() => api.adminSessions({ limit: 100 }), [])

  if (error) return <p className="form-error" role="alert">{error.message}</p>
  if (loading || !data) return <p className="entry-meta" aria-live="polite">Loading…</p>

  return (
    <>
      <p className="entry-meta">
        {/* `SW-ADR-106`: no IP, no user agent, and the response model has no
            field for either. Answering "who is signed in" does not require
            handing an administrator a location history. */}
        {data.total} live session{data.total === 1 ? '' : 's'}. SpendWise does not
        show where a session is signed in from.
      </p>
      <div className="table-wrap">
        <table className="table" data-testid="admin-sessions">
          <thead>
            <tr>
              <th scope="col">Account</th>
              <th scope="col">Signed in</th>
              <th scope="col">Last seen</th>
              <th scope="col">Expires</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((s) => (
              <tr key={s.id}>
                <td className="sw-num">#{s.user_id}</td>
                <td className="entry-meta">{longDate(s.issued_at.slice(0, 10))}</td>
                <td className="entry-meta">{longDate(s.last_seen_at.slice(0, 10))}</td>
                <td className="entry-meta">{longDate(s.expires_at.slice(0, 10))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

// ── audit ──────────────────────────────────────────────────────────────────
function Audit() {
  const [{ data, error, loading }] = useAsync(() => api.adminAudit({ limit: 100 }), [])

  if (error) return <p className="form-error" role="alert">{error.message}</p>
  if (loading || !data) return <p className="entry-meta" aria-live="polite">Loading…</p>

  return (
    <>
      <p className="entry-meta">
        Every administrative action, and every read of these pages. Written in
        the same transaction as the change it records, and immutable at the
        database — {data.total} entries.
      </p>
      <ul className="audit" data-testid="admin-audit">
        {data.items.map((row) => (
          <li key={row.id} className="audit-row">
            <span className="entry-meta audit-when">
              {longDate(row.created_at.slice(0, 10))}
            </span>
            {/* The sentence is rendered SERVER-SIDE (`P-ADM-08`). A client
                assembling it would need to know all nine action types and
                would print `[object Object]` for the tenth. */}
            <span className="audit-what">
              Administrator #{row.admin_id} {row.sentence}.
            </span>
          </li>
        ))}
      </ul>
    </>
  )
}
