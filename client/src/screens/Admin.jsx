import { useCallback, useEffect, useState } from 'react'
import { api } from '../lib/api.js'
import { days, longDate, dollars, shortDate } from '../lib/money.js'
import { PERIODS, identify, today } from '../lib/period.js'
import Bars from '../components/charts/Bars.jsx'
import LinePlot from '../components/charts/LinePlot.jsx'
import { CountUp, Odometer } from '../lib/motion.js'

/**
 * Administration.
 *
 * **The money line moved, once, and this is where it now sits.**
 *
 * `SRC-001 §4.2` was the client's own permission matrix — *"See anyone else's
 * expense amounts | user: no | admin: **no**"*, their bold — and `SW-ADR-129`
 * built the whole admin data path around it. `CR-001` reverses that one clause
 * and nothing beside it. An administrator may now see, for ONE person at a
 * time:
 *
 *     the total over a range · the count · the daily average · the line plot
 *
 * and may still not see **which categories** the money went to, **what any
 * expense was for**, or any individual row — at any granularity. That is not a
 * promise this file keeps. `admin_user_daily()` is `SECURITY DEFINER` and its
 * `RETURNS TABLE` clause declares three columns — day, total, count — so there
 * is no fourth to render even if a component asked for one (`SW-ADR-151`,
 * using `SW-ADR-129`'s mechanism against a line the client has moved rather
 * than abandoned).
 *
 * Concretely, for anyone editing below: **no `Donut`, no `Ribbon`, no
 * `EntryList` on the detail pane, and no import of any of them in this file.**
 * If you are reaching for one, the thing you want does not exist on purpose.
 *
 * Everything else here still counts accounts, sessions, actions or rows: the
 * tables show no money, the overview shows no money, and every read of the one
 * pane that does is written to the audit log.
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
    <div className="admin">
      <header className="page-head admin-head">
        <div>
          <p className="sw-eyebrow">Console</p>
          <h1 className="page-title">Administration</h1>
          <p className="entry-meta admin-lede">
            Accounts and activity. Opening one account shows how much that
            person spent over a range and never what they spent it on: no
            category, no description, no single entry. That limit is enforced
            by the database, not by this page, and every look is audited.
          </p>
        </div>
      </header>

      <div className="tabs" role="tablist" aria-label="Administration sections">
        {TABS.map((t) => (
          <button key={t.id} type="button" role="tab" className="tab"
                  id={`admin-tabbtn-${t.id}`} aria-controls="admin-tabpanel"
                  aria-selected={tab === t.id} data-testid={`admin-tab-${t.id}`}
                  onClick={() => setTab(t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Keyed on the tab so each section arrives with a short fade instead of
          swapping in place. 240ms, opacity and a few pixels only. */}
      <div key={tab} id="admin-tabpanel" role="tabpanel" className="admin-panel"
           aria-labelledby={`admin-tabbtn-${tab}`}>
        {tab === 'overview' && <Overview />}
        {tab === 'accounts' && <Accounts me={principal} />}
        {tab === 'sessions' && <Sessions />}
        {tab === 'audit' && <Audit />}
      </div>
    </div>
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
  if (loading || !data) {
    return (
      <div className="card admin-stats admin-stats-loading">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="admin-stat" aria-hidden="true">
            <span className="skeleton admin-skel-label" />
            <span className="skeleton admin-skel-value" />
          </div>
        ))}
        <p className="visually-hidden" aria-live="polite">Loading…</p>
      </div>
    )
  }

  const count = (n) => String(n)

  return (
    <>
      <section className="card card-statement admin-stats sw-stagger" aria-label="Totals"
               data-testid="admin-overview">
        <Stat label="Accounts" value={data.accounts_total} testId="stat-accounts"
              hint={`${data.admins} administrator${data.admins === 1 ? '' : 's'}`} />
        {/* PAUSED and CLOSED are separate figures, and the hint says both.
            They were one number until `CR-001 §5.2` — closing an account sets
            `is_active = false` too, so a closed account was reported as a
            paused one and the dashboard could not say how many people had
            actually left. The three now sum to `accounts_total`. */}
        <Stat label="Active" value={data.accounts_active} testId="stat-active"
              hint={`${data.accounts_deactivated} paused · ${data.accounts_deleted} closed`} />
        <Stat label="Signed in now" value={data.sessions_live} testId="stat-sessions"
              hint="live sessions across all accounts" />
        <Stat label="Expenses recorded" value={data.expenses_recorded}
              testId="stat-expenses" hint="a count of rows, never a sum" />
      </section>

      <section className="panels admin-panels sw-stagger" aria-label="Activity">
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

/**
 * One figure in the overview strip. COUNTS only, so the count-up formats with
 * `String` and never with `dollars`: nothing on this tab is money. The final
 * figure is the real text from the first frame (tests read it at once).
 */
function Stat({ label, value, hint, testId }) {
  return (
    <div className="admin-stat">
      <p className="card-label">{label}</p>
      <p className="card-value admin-stat-value sw-num">
        <CountUp value={value} format={String} split={false} data-testid={testId} />
      </p>
      {hint && <p className="entry-meta">{hint}</p>}
    </div>
  )
}

// ── accounts ───────────────────────────────────────────────────────────────

/**
 * One word for the account's state, derived in ONE place so the table and the
 * detail pane cannot disagree.
 *
 * Deleted beats deactivated: `DELETE /api/auth/me` sets `deleted_at` **and**
 * `is_active = false` in the same transaction (`CR-001 §2`), so a closed
 * account is also an inactive one and reporting it as merely "deactivated"
 * would hide the thing the administrator is looking for.
 *
 * `u.deleted` missing entirely — an older response, or a client running ahead
 * of a deploy — reads as `false` and the account shows its `is_active` state.
 * That is the right failure: it under-reports rather than inventing a closure.
 */
function statusOf(u) {
  if (u.deleted) return 'deleted'
  return u.is_active ? 'active' : 'deactivated'
}

const DOTS = { active: 'ok-dot', deactivated: 'off-dot', deleted: 'gone-dot' }

/** The dot is decoration; the WORD carries it. Never colour alone (`SW-ADR-118`). */
function Status({ user }) {
  const state = statusOf(user)
  return (
    <span className={`admin-status admin-status-${state}`}>
      <span className={DOTS[state]} aria-hidden="true" />
      {state}
    </span>
  )
}

/** Two letters for the account's monogram, drawn by CSS from a data attribute
    so it is decoration only: not in the accessible name, not in innerText. */
function initials(name) {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean)
  return ((parts[0]?.[0] || '') + (parts.length > 1 ? parts[parts.length - 1][0] : '')).toUpperCase()
}

/**
 * The `deleted` filter. Three states, because two would be a lie: the server's
 * default is not "not deleted", it is **everything** (`CR-001 §2` — "an
 * administrator looking for someone who has left must be able to find them"),
 * and a two-position toggle has nowhere to put that.
 *
 * `value: undefined` is what omits the parameter — `q()` drops `undefined` and
 * keeps `false`, so "Not deleted" really does send `deleted=false` rather than
 * silently falling back to the default.
 */
const DELETED_FILTERS = [
  { id: 'any', label: 'All accounts', value: undefined },
  { id: 'false', label: 'Not deleted', value: false },
  { id: 'true', label: 'Deleted only', value: true },
]

function Accounts({ me }) {
  const [q, setQ] = useState('')
  const [deleted, setDeleted] = useState('any')
  // The ROW, not an id. Held here rather than derived from `data.items` because
  // restoring an account removes it from a `deleted=true` list, and a pane that
  // vanished the instant it succeeded would take its own confirmation with it.
  const [viewing, setViewing] = useState(null)
  const [notice, setNotice] = useState(null)
  const [error, setError] = useState(null)
  const [{ data, loading }, reload] = useAsync(
    () => api.adminUsers({
      q: q || undefined, limit: 100,
      deleted: DELETED_FILTERS.find((f) => f.id === deleted).value,
    }), [q, deleted])

  const act = async (label, fn) => {
    setError(null)
    setNotice(null)
    try {
      const out = await fn()
      setNotice(typeof out === 'object' && out?.token
        ? `Reset code for that account. Copy it now, it is shown once: ${out.token}`
        : label)
      await reload()
    } catch (err) {
      setError(err)
    }
  }

  // The pane REPLACES the table rather than sitting under it. One person's
  // figures beside a list of everyone invites reading the figures as the list's
  // — and at phone width the table's scroll container would swallow the pane.
  if (viewing) {
    return (
      <UserDetail key={viewing.id} row={viewing} onChanged={reload}
                  onBack={() => setViewing(null)} />
    )
  }

  return (
    <>
      <div className="admin-toolbar">
      <div className="row-form admin-search">
        <div className="field field-grow">
          <label htmlFor="admin-search" className="visually-hidden">Search accounts</label>
          <input id="admin-search" placeholder="Search by email or name"
                 data-testid="admin-search" value={q}
                 onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="filters" role="group" aria-label="Filter by deletion">
        {DELETED_FILTERS.map((f) => (
          <button key={f.id} type="button" className="chip"
                  data-testid={`admin-deleted-${f.id}`}
                  aria-pressed={deleted === f.id}
                  onClick={() => setDeleted(f.id)}>
            {f.label}
          </button>
        ))}
      </div>
      </div>

      {error && (
        <p className="form-error sw-pop" role="alert" data-testid="admin-error">
          {error.code === 'CONFLICT'
            ? 'That would leave no active administrator.'
            : error.code === 'FORBIDDEN'
            ? 'An administrator cannot reset another administrator. Demote them first.'
            : error.message}
        </p>
      )}
      {notice && (
        <p className="ok notice sw-pop" role="status" data-testid="admin-notice">{notice}</p>
      )}

      {loading && !data ? <p className="entry-meta" aria-live="polite">Loading…</p> : (
        <div className="table-wrap admin-table-wrap sw-enter">
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
                  <td className="admin-account" data-initials={initials(u.display_name)}>
                    <span className="cell-strong">{u.display_name}</span>
                    <span className="entry-meta cell-sub">{u.email}</span>
                  </td>
                  <td>
                    {u.role === 'admin'
                      ? <span className="pill pill-gold">admin</span>
                      : <span className="entry-meta">user</span>}
                  </td>
                  <td><Status user={u} /></td>
                  {/* A COUNT. There is still no column here that could hold a
                      sum: `CR-001` opened one person's total on the detail
                      pane, deliberately behind a click and an audit row, and
                      not a column an administrator can scan down. */}
                  <td className="num sw-num">{u.expense_count}</td>
                  <td className="entry-meta">
                    {u.last_activity ? shortDate(u.last_activity) : 'never'}
                  </td>
                  <td className="row-actions">
                    <button type="button" className="btn btn-quiet btn-sm admin-act admin-act-view"
                            data-testid={`view-${u.id}`}
                            onClick={() => setViewing(u)}>
                      View
                    </button>
                    <button type="button" className="btn btn-quiet btn-sm admin-act"
                            data-testid={`revoke-${u.id}`}
                            onClick={() => act('Signed out.', () => api.adminRevoke(u.id))}>
                      Sign out
                    </button>
                    {/* One action restores a deleted account: `is_active: true`
                        also clears `deleted_at` (`CR-001 §2`). So this is the
                        same call with a truthful label rather than a fourth
                        button — "Reactivate" on a closed account would leave
                        the person wondering which half it undid. */}
                    <button type="button"
                            className="btn btn-quiet btn-sm admin-act"
                            data-testid={`toggle-active-${u.id}`}
                            onClick={() => act(
                              u.deleted ? 'Restored.' : u.is_active ? 'Deactivated.' : 'Reactivated.',
                              () => api.adminSetActive(u.id, !u.is_active))}>
                      {u.deleted ? 'Restore' : u.is_active ? 'Deactivate' : 'Reactivate'}
                    </button>
                    <button type="button" className="btn btn-quiet btn-sm admin-act"
                            data-testid={`toggle-role-${u.id}`}
                            onClick={() => act('Role changed.',
                              () => api.adminSetRole(u.id, u.role === 'admin' ? 'user' : 'admin'))}>
                      {u.role === 'admin' ? 'Demote' : 'Promote'}
                    </button>
                    <button type="button" className="btn btn-quiet btn-sm admin-act"
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

// ── one person ─────────────────────────────────────────────────────────────
/**
 * The detail pane. **The only screen in SpendWise where one person sees
 * another person's money**, and the only one that will ever be.
 *
 * What it shows is fixed by the response and not by taste: a total, a count, a
 * daily average and a day-by-day line. `AdminUserSpending` carries no
 * `by_category`, no description and no expense row — grep it for `categor` and
 * there is nothing to find — so the temptation to "just add the breakdown while
 * we are here" has nothing to read. **Do not add a `Donut`, a `Ribbon` or an
 * `EntryList` below.** That boundary is the entire content of `CR-001`; the
 * client asked for *"the expenses that are happening **not the categories spent
 * on**"* and drew the line themselves.
 *
 * `data.user` is a whole `AdminUser` — the same row the table shows — so every
 * fact below prefers it and falls back to `row` only until the first response
 * lands, or if it never does. That ordering is what makes Restore honest: the
 * status a person reads after clicking it came back from the server, and is not
 * this component congratulating itself.
 */
function UserDetail({ row, onBack, onChanged }) {
  const now = today()
  const [range, setRange] = useState(() => PERIODS[0].range(now))
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState(null)

  const [{ data, error, loading }, reload] = useAsync(
    () => api.adminUserSpending(row.id, { from: range.from, to: range.to }),
    [row.id, range.from, range.to])

  // Keyed on the PERSON and not the range: a session is not in a date window,
  // and refetching it on every chip would write an audit row per click for an
  // answer that had not changed.
  const [{ data: sessions }] = useAsync(
    () => api.adminSessions({ user_id: row.id, limit: 1 }), [row.id])

  const who = data?.user || row
  const active = identify(range, now)

  const restore = async () => {
    setBusy(true)
    setActionError(null)
    try {
      // ONE call. `is_active: true` on a deleted account also clears
      // `deleted_at` (`CR-001 §2`) — restoring is one action, not two, and a
      // client that made it two could leave an account half-restored if the
      // second request failed.
      await api.adminSetActive(row.id, true)
      await reload()          // the pane's own copy of who they are
      await onChanged()       // and the table waiting behind it
    } catch (err) {
      setActionError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="detail admin-detail sw-enter" data-testid="admin-user-detail"
             aria-label={`${who.display_name}, account detail`}>
      <header className="page-head admin-detail-head">
        <div className="admin-detail-who" data-initials={initials(who.display_name)}>
          <h2 className="section-title">{who.display_name}</h2>
          <p className="entry-meta">{who.email}</p>
        </div>
        <button type="button" className="btn btn-quiet" onClick={onBack}
                data-testid="admin-user-back">
          Back to accounts
        </button>
      </header>

      <dl className="card facts admin-facts">
        <div>
          <dt>Status</dt>
          <dd data-testid="admin-user-status"><Status user={who} /></dd>
        </div>
        <div>
          <dt>Expenses recorded</dt>
          {/* LIFETIME, from `admin_expense_stats()` — deliberately not
              `data.count`, which counts only the selected range. Two counts a
              few centimetres apart need the labels to say which is which, and
              "Entries" below carries the range's dates under it. */}
          <dd className="sw-num" data-testid="admin-user-expense-count">
            {who.expense_count}
          </dd>
        </div>
        <div>
          <dt>Last activity</dt>
          <dd data-testid="admin-user-last-activity">
            {who.last_activity ? longDate(who.last_activity) : 'never'}
          </dd>
        </div>
        <div>
          <dt>Signed in now</dt>
          {/* `SW-ADR-106` still holds: a count, never where from. */}
          <dd className="sw-num" data-testid="admin-user-sessions">
            {sessions ? sessions.total : '—'}
          </dd>
        </div>
        <div>
          <dt>Role</dt>
          <dd>{who.role === 'admin' ? <span className="pill pill-gold">admin</span> : 'user'}</dd>
        </div>
      </dl>

      {actionError && (
        <p className="form-error sw-pop" role="alert" data-testid="admin-user-action-error">
          {actionError.message}
        </p>
      )}

      {statusOf(who) === 'deleted' && (
        <div className="card card-danger admin-closed sw-enter">
          <p className="card-desc">
            <strong>This account was closed by the person who owns it.</strong>{' '}
            Nothing was erased: every expense and category is still attached to
            it, and their email address is still held. Restoring it clears the
            closure and lets them sign in again.
          </p>
          <button type="button" className="btn" onClick={restore}
                  data-testid={`restore-${row.id}`}
                  aria-disabled={busy ? 'true' : undefined}>
            {busy ? 'Restoring…' : 'Restore this account'}
          </button>
        </div>
      )}

      {/* Not `PeriodPicker`. It owns two things this pane must not have: the
          `period-*` test ids, which would collide with the person's own picker
          in any test that walks the whole app, and `writeState` — the URL's
          `?from=&to=` belongs to the ADMINISTRATOR'S dashboard period, and an
          admin glancing at someone's year would silently rewrite their own. The
          list itself is shared, which is the part that could actually drift. */}
      <div className="periods" role="group" aria-label="Period">
        {PERIODS.map((p) => (
          <button key={p.id} type="button" className="chip"
                  data-testid={`admin-period-${p.id}`}
                  aria-pressed={active === p.id}
                  aria-disabled={loading ? 'true' : undefined}
                  onClick={() => !loading && setRange(p.range(now))}>
            {p.label}
          </button>
        ))}
      </div>

      {error ? (
        <p className="form-error" role="alert" data-testid="admin-user-error">
          {error.message}
        </p>
      ) : !data ? (
        <p className="entry-meta" aria-live="polite">Loading…</p>
      ) : (
        <>
          <section className="cards admin-figures sw-stagger"
                   aria-label="Spending in the selected range">
            <article className="card card-statement admin-figure-total">
              <p className="card-label">Total</p>
              {/* `dollars(total_paise)`, never the `total` string the response
                  also carries. That string is a plain decimal — 3790.49 — and
                  printing it would put an ungrouped number beside every
                  grouped one in the product (`SW-ADR-157`). The integer is
                  the value; the formatting is `lib/money.js`'s job. */}
              {/* An Odometer, so a period change ROLLS the figure in place
                  rather than swapping it. Its text is `dollars(total_paise)`,
                  exactly as before; the reels are aria-hidden decoration. */}
              <p className="card-value sw-num">
                <Odometer value={data.total_paise} format={dollars}
                          data-testid="admin-user-total" />
              </p>
              <p className="entry-meta">{data.from} to {data.to}</p>
            </article>

            <article className="card">
              <p className="card-label">Entries</p>
              <p className="card-value sw-num">
                <Odometer value={data.count} format={String} split={false}
                          data-testid="admin-user-count" />
              </p>
              <p className="entry-meta">a count of expenses, not a list of them</p>
            </article>

            <article className="card">
              <p className="card-label">Daily average</p>
              {/* `daily_average_paise` is `int | None` on the model, produced by
                  the same helper as the person's own summary: no day elapsed
                  means no average, never 0.00 (`SW-ADR-053`). None of the five
                  chips can build a wholly-future range, so the branch is rarely
                  taken — but $0.00 standing in for "no answer yet" reads as
                  "this person spends nothing", and that is a claim about
                  someone else's money that nothing here is entitled to make. */}
              <p className="card-value sw-num">
                {data.daily_average_paise === null
                  ? <span data-testid="admin-user-average">Not yet</span>
                  : <Odometer value={data.daily_average_paise} format={dollars}
                              data-testid="admin-user-average" />}
              </p>
              <p className="entry-meta">over {days(data.days_elapsed)}</p>
            </article>
          </section>

          {/* ONE chart, and there is no second one coming. A donut here would
              need `by_category`; the response has no such field and no
              parameter asks for one, so this is the exact spot where the line
              `CR-001` draws stops being a rule and becomes a missing key. */}
          <article className="card admin-plot sw-enter">
            <h3 className="card-heading">Spending over time</h3>
            <LinePlot days={data.by_day} />
            {data.count === 0 && (
              <p className="entry-meta" data-testid="admin-user-empty">
                Nothing recorded in this range. The flat line is the answer, not
                a failure to load.
              </p>
            )}
          </article>
        </>
      )}
    </section>
  )
}

// ── sessions ───────────────────────────────────────────────────────────────
function Sessions() {
  const [{ data, error, loading }] = useAsync(() => api.adminSessions({ limit: 100 }), [])

  if (error) return <p className="form-error" role="alert">{error.message}</p>
  if (loading || !data) return <p className="entry-meta" aria-live="polite">Loading…</p>

  return (
    <>
      <p className="entry-meta admin-intro">
        {/* `SW-ADR-106`: no IP, no user agent, and the response model has no
            field for either. Answering "who is signed in" does not require
            handing an administrator a location history. */}
        {data.total} live session{data.total === 1 ? '' : 's'}. SpendWise does not
        show where a session is signed in from.
      </p>
      <div className="table-wrap admin-table-wrap sw-enter">
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
      <p className="entry-meta admin-intro">
        Every administrative action, and every read of these pages. Written in
        the same transaction as the change it records, and immutable at the
        database. {data.total} entries.
      </p>
      <div className="card admin-audit-card sw-enter">
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
      </div>
    </>
  )
}
