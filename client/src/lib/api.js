/**
 * The HTTP layer. One place that knows the envelope, and one place that knows
 * what a 401 means.
 *
 * The session is an httpOnly cookie (`SRC-001 §10.4`), so there is no token to
 * attach and nothing here reads `document.cookie` — script cannot, which is the
 * point. `credentials: 'same-origin'` is the default for same-origin requests
 * and is written out anyway, because the one-origin deployment (`SW-ADR-020`)
 * is a decision and not an accident.
 */

/** Every non-2xx arrives as `{error: {code, message, field?}}` (`SW-ADR-051`). */
export class ApiError extends Error {
  constructor(status, body) {
    const envelope = body && body.error ? body.error : {}
    super(envelope.message || 'Something went wrong.')
    this.name = 'ApiError'
    this.status = status
    this.code = envelope.code || 'INTERNAL'
    this.field = envelope.field || null
  }
}

// ── the single-redirect guard, and session EPOCHS ───────────────────────────
// E3-S7 AC2: two concurrent 401s produce exactly ONE redirect. The dashboard
// fires the summary and the entry list together, so an expired session returns
// two 401s within a millisecond of each other; without this the app navigates,
// then navigates again, and the second navigation wipes the reason banner and
// the draft the first one saved.
//
// Three rules on top of that latch, each closing a reported glitch:
//
//   1. The guard starts DISARMED and is armed only by `startSession()`, after a
//      successful me / login / register. A first visit is not a session.
//   2. The four AUTH calls (login, register, me, logout) never fire it. Their
//      401 means "wrong password" or "no session", not "your session ended",
//      and a sign-in form that answers a typo with "Your session ended" is
//      wrong in a way that depends on history, which is why it felt random.
//   3. Every request belongs to the EPOCH it was sent in. Signing in, signing
//      out and a session ending each start a new epoch and abort everything in
//      flight. A response from an older epoch is DROPPED: its promise never
//      settles, so the unmounting screen neither fires the handler (a late 401
//      after a deliberate sign-out, or one that bounces the NEXT person out)
//      nor flashes "Could not load" while it waits to be replaced. Every caller
//      of a stale request belongs to a screen that is going away.
let sessionEndedHandler = null
let armed = false
let epoch = 0
let controller = new AbortController()
const NEVER = new Promise(() => {})

export function onSessionEnded(handler) {
  sessionEndedHandler = handler
}

/** Abort everything in flight and invalidate it. */
function nextEpoch() {
  epoch += 1
  controller.abort()
  controller = new AbortController()
}

/** A session is now known to exist: new epoch, guard armed. */
export function startSession() {
  nextEpoch()
  armed = true
}

/** A deliberate sign-out: new epoch, guard disarmed BEFORE the logout call, so
    nothing still in flight from the old screen can raise a false banner. */
export function stopSession() {
  nextEpoch()
  armed = false
}

function endSession(err, sentIn) {
  if (!armed || sentIn !== epoch) return
  armed = false
  nextEpoch()
  if (sessionEndedHandler) sessionEndedHandler(err)
}

async function request(method, path, body, { auth = false } = {}) {
  const sentIn = epoch
  const { signal } = controller
  let response
  try {
    response = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (cause) {
    if (signal.aborted || sentIn !== epoch) return NEVER
    // The network, not the server. Distinguished from a 500 because the retry
    // advice differs and because "Something went wrong" over a dropped wifi
    // connection sends people to look for a bug that is not there.
    const err = new ApiError(0, { error: { code: 'NETWORK', message: 'Could not reach SpendWise. Check your connection and try again.' } })
    err.cause = cause
    throw err
  }

  let payload = null
  if (response.status !== 204) {
    try {
      payload = await response.json()
    } catch {
      payload = null
    }
  }
  if (sentIn !== epoch) return NEVER

  if (!response.ok) {
    const err = new ApiError(response.status, payload)
    if (response.status === 401 && !auth) endSession(err, sentIn)
    throw err
  }
  return payload
}

const AUTH = { auth: true }

const q = (params) => {
  const search = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') search.set(k, String(v))
  }
  const s = search.toString()
  return s ? `?${s}` : ''
}

export const api = {
  register: (body) => request('POST', '/api/auth/register', body, AUTH),
  login: (body) => request('POST', '/api/auth/login', body, AUTH),
  logout: () => request('POST', '/api/auth/logout', undefined, AUTH),
  me: () => request('GET', '/api/auth/me', undefined, AUTH),

  updateMe: (body) => request('PATCH', '/api/auth/me', body),
  changePassword: (body) => request('POST', '/api/auth/password', body),
  deactivate: () => request('POST', '/api/auth/deactivate'),
  // Two names for two different promises (`CR-001 §2`, `SW-ADR-150`).
  // `deactivate` pauses an account; this CLOSES it — 204, cookie cleared,
  // every session revoked, `deleted_at` set, and not one row of theirs
  // touched. They stay separate here precisely because the difference is
  // invisible in the response: a single `close(kind)` helper is how a button
  // labelled "Delete" ends up calling the other one, which is the failure
  // `SW-ADR-148` named and CR-001 repeats.
  deleteMe: () => request('DELETE', '/api/auth/me'),
  exportMine: () => request('GET', '/api/auth/export'),

  categories: () => request('GET', '/api/categories'),
  createCategory: (body) => request('POST', '/api/categories', body),
  updateCategory: (id, body) => request('PATCH', `/api/categories/${id}`, body),
  deleteCategory: (id) => request('DELETE', `/api/categories/${id}`),

  summary: (params) => request('GET', `/api/expenses/summary${q(params)}`),
  expenses: (params) => request('GET', `/api/expenses${q(params)}`),
  createExpense: (body) => request('POST', '/api/expenses', body),
  updateExpense: (id, body) => request('PATCH', `/api/expenses/${id}`, body),
  deleteExpense: (id) => request('DELETE', `/api/expenses/${id}`),

  // ── admin. Every one of these is 403 for a `user`, enforced on the ROUTER
  // (`SRC-001 §4.3`) — hiding the link is cosmetic and the client knows it.
  adminOverview: () => request('GET', '/api/admin/overview'),
  // `deleted=true|false` rides through `q()` like any other param — and note
  // that `q()` drops `null`/`undefined`/`''` and NOT falsy values, which is the
  // only reason `deleted: false` survives the trip. OMITTING it includes the
  // deleted accounts (`CR-001 §2`): an administrator looking for someone who
  // has left must be able to find them, so the default cannot be a filter.
  adminUsers: (params) => request('GET', `/api/admin/users${q(params || {})}`),
  adminSessions: (params) => request('GET', `/api/admin/sessions${q(params || {})}`),
  adminAudit: (params) => request('GET', `/api/admin/audit${q(params || {})}`),
  adminRevoke: (id) => request('POST', `/api/admin/users/${id}/revoke-sessions`),
  adminSetActive: (id, is_active) =>
    request('POST', `/api/admin/users/${id}/active`, { is_active }),
  adminSetRole: (id, role) => request('POST', `/api/admin/users/${id}/role`, { role }),
  adminReset: (id) => request('POST', `/api/admin/users/${id}/reset`),

  // The ONE admin call that answers "how much" (`CR-001`, `SW-ADR-151`), and it
  // answers it three columns at a time: day, total, count. There is no
  // `by_category` on the response and no parameter here that could ask for one
  // — `admin_user_daily()`'s `RETURNS TABLE` clause is what makes that true,
  // not this line. `params` carries `from` and `to`; both are required, and the
  // server refuses the same way `/api/expenses/summary` does rather than
  // guessing a range.
  adminUserSpending: (id, params) =>
    request('GET', `/api/admin/users/${id}/spending${q(params)}`),
}
