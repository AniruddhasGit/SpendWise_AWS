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

// ── the single-redirect guard ──────────────────────────────────────────────
// E3-S7 AC2: two concurrent 401s produce exactly ONE redirect. The dashboard
// fires the summary and the entry list together, so an expired session returns
// two 401s within a millisecond of each other; without this the app navigates,
// then navigates again, and the second navigation wipes the reason banner and
// the draft the first one saved.
let sessionEndedHandler = null
let alreadyEnded = false

export function onSessionEnded(handler) {
  sessionEndedHandler = handler
}

/** Reset after a successful sign-in, so the NEXT expiry can fire again. */
export function armSessionGuard() {
  alreadyEnded = false
}

function endSession(err) {
  if (alreadyEnded) return
  alreadyEnded = true
  if (sessionEndedHandler) sessionEndedHandler(err)
}

async function request(method, path, body) {
  let response
  try {
    response = await fetch(path, {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (cause) {
    // The network, not the server. Distinguished from a 500 because the retry
    // advice differs and because "Something went wrong" over a dropped wifi
    // connection sends people to look for a bug that is not there.
    const err = new ApiError(0, { error: { code: 'NETWORK', message: 'Could not reach SpendWise. Check your connection and try again.' } })
    err.cause = cause
    throw err
  }

  if (response.status === 204) return null

  let payload = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const err = new ApiError(response.status, payload)
    if (response.status === 401) endSession(err)
    throw err
  }
  return payload
}

const q = (params) => {
  const search = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') search.set(k, String(v))
  }
  const s = search.toString()
  return s ? `?${s}` : ''
}

export const api = {
  register: (body) => request('POST', '/api/auth/register', body),
  login: (body) => request('POST', '/api/auth/login', body),
  logout: () => request('POST', '/api/auth/logout'),
  me: () => request('GET', '/api/auth/me'),

  categories: () => request('GET', '/api/categories'),
  createCategory: (body) => request('POST', '/api/categories', body),
  updateCategory: (id, body) => request('PATCH', `/api/categories/${id}`, body),
  deleteCategory: (id) => request('DELETE', `/api/categories/${id}`),

  summary: (params) => request('GET', `/api/expenses/summary${q(params)}`),
  expenses: (params) => request('GET', `/api/expenses${q(params)}`),
  createExpense: (body) => request('POST', '/api/expenses', body),
  updateExpense: (id, body) => request('PATCH', `/api/expenses/${id}`, body),
  deleteExpense: (id) => request('DELETE', `/api/expenses/${id}`),
}
