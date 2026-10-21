import { useEffect, useId, useRef, useState } from 'react'
import DatePicker from './DatePicker.jsx'
import { createPortal } from 'react-dom'
import { plain } from '../lib/money.js'
import { today } from '../lib/period.js'

const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

/**
 * The add / edit expense panel. A real dialog (`DESIGN-SYSTEM.md §5`):
 *
 * - focus is trapped while open and **restored to the trigger on close**
 * - Escape closes; the background is `inert`
 * - a dirty form confirms before discarding
 * - the submit control disables on first click and stays disabled until the
 *   response settles
 * - **the entry does not appear in the list before the server confirms it**
 *
 * That last one is E3-S5's sharpest criterion and the reason there is no
 * optimistic insert here. An optimistic row is a number the person can see
 * that the server has not accepted; if the write then fails, the total they
 * were shown was never true. In a product whose entire job is to be right
 * about money, a fast wrong number is worse than a slow right one.
 */
export default function ExpensePanel({ open, editing, categories, draft, onDraft,
                                       onSubmit, onClose }) {
  const id = useId()
  const panel = useRef(null)
  const returnFocusTo = useRef(null)
  const [busy, setBusy] = useState(false)
  // The Escape listener is bound once per open; `tryClose` closes over `dirty`,
  // which changes on every keystroke. A ref keeps the listener current without
  // re-binding it forty times while someone types an amount.
  const tryCloseRef = useRef(() => {})
  const [error, setError] = useState(null)

  const blank = { amount: '', spent_on: today(), category_id: '', description: '' }
  const [form, setForm] = useState(blank)
  const [pristine, setPristine] = useState(blank)

  useEffect(() => {
    if (!open) return
    returnFocusTo.current = document.activeElement
    // An edit starts from the row; a create starts from the DRAFT, which is
    // what survived a session ending mid-typing (E3-S7 AC3).
    const start = editing
      ? { amount: plain(editing.amount_paise), spent_on: editing.spent_on,
          category_id: editing.category_id ?? '', description: editing.description ?? '' }
      : { ...blank, ...(draft || {}) }
    setForm(start)
    setPristine(start)
    setError(null)
    setBusy(false)
    // The first field, not the dialog — a person opening this is about to type
    // a number, and one keystroke saved on the commonest action in the product
    // is worth more than the announcement of the container.
    const timer = setTimeout(() => {
      panel.current?.querySelector('input')?.focus()
    }, 0)
    return () => clearTimeout(timer)
  }, [open, editing])

  const dirty = JSON.stringify(form) !== JSON.stringify(pristine)

  // Keep the draft outside this component so it survives the panel unmounting
  // — including the unmount that a session-expiry redirect causes.
  useEffect(() => {
    if (open && !editing && dirty) onDraft(form)
  }, [form, open, editing, dirty])

  /**
   * Focus RESTORED to the trigger — on a timeout, and that is not a hack.
   *
   * The trigger lives inside `.shell`, which is `inert` while the panel is
   * open. An inert subtree is removed from the focus system entirely, so
   * `focus()` called synchronously here is a silent no-op: focus falls to
   * <body> and the next Tab starts from the top of the document. Clearing
   * inert happens in the dashboard's effect, which runs after this commit.
   * A zero timeout is the first moment both have happened.
   */
  //
  // A zero timeout is enough after Escape (a discrete event: React flushes
  // the close synchronously). After a SAVE it is not: the close is set after
  // an await, the commit is batched, and the timeout can fire before the
  // effect that clears `inert` has run — focus() is then a no-op and focus
  // lands on <body>. So the restore waits, frame by frame, until the trigger
  // is out of every inert subtree (or gives up after ~10 frames).
  const restoreFocus = () => {
    const trigger = returnFocusTo.current
    const attempt = (left) => {
      if (!trigger?.isConnected) return
      if (trigger.closest('[inert]')) {
        if (left > 0) requestAnimationFrame(() => attempt(left - 1))
        return
      }
      trigger.focus?.()
    }
    setTimeout(() => attempt(10), 0)
  }

  // THE DIALOG makes the rest of the application inert, and it does it to the
  // whole shell — not to the pane it happens to be rendered beside.
  //
  // The first version let the dashboard mark its own content inert. That was
  // correct until the sidebar, the mobile top bar and the footer sign-out
  // moved OUT of the dashboard, at which point a modal left the entire
  // application chrome clickable behind it and nothing said so. A dialog is
  // responsible for the whole background being inert, so it owns the flag.
  useEffect(() => {
    if (!open) return
    const shellEl = document.querySelector('.app') || document.getElementById('root')
    if (shellEl) shellEl.inert = true
    return () => { if (shellEl) shellEl.inert = false }
  }, [open])

  // ESCAPE IS BOUND TO THE DOCUMENT, not to the panel.
  //
  // Bound to the panel it only fires when focus is already inside — and focus
  // arrives on a zero timeout, because the trigger sits in a subtree that
  // becomes `inert` in the same commit and an inert subtree cannot hold focus.
  // Between the paint and that timeout there is a window in which the dialog
  // is open and Escape does nothing. It is a handful of milliseconds and a
  // browser test caught it, but it is a real one: the first thing an impatient
  // person does with a dialog they opened by mistake is hit Escape.
  useEffect(() => {
    if (!open) return
    const onEscape = (event) => {
      if (event.key !== 'Escape') return
      // Escape inside the date field's calendar closes only the calendar
      if (event.target?.closest?.('.date-pop')) return
      event.stopPropagation()
      tryCloseRef.current()
    }
    document.addEventListener('keydown', onEscape, true)
    return () => document.removeEventListener('keydown', onEscape, true)
  }, [open])

  const tryClose = () => {
    if (dirty && !window.confirm('Discard this expense?')) return
    if (!editing) onDraft(null)
    onClose()
    restoreFocus()
  }

  tryCloseRef.current = tryClose

  const onKeyDown = (event) => {
    if (event.key !== 'Tab') return
    // The trap. `inert` on the background handles pointer and screen-reader
    // access; Tab still needs wrapping, because inert is applied to a sibling
    // and the browser will happily tab to the address bar and back in.
    const items = [...panel.current.querySelectorAll(FOCUSABLE)]
      .filter((el) => !el.hasAttribute('disabled') && el.offsetParent !== null)
    if (!items.length) return
    const first = items[0]
    const last = items[items.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  const submit = async (event) => {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await onSubmit({
        amount: form.amount.trim(),
        spent_on: form.spent_on,
        category_id: form.category_id === '' ? null : Number(form.category_id),
        description: form.description.trim() === '' ? null : form.description.trim(),
      })
      if (!editing) onDraft(null)
      onClose()
      restoreFocus()
    } catch (err) {
      // The server's own sentence, on the field the server named. Not a
      // second copy of the rule written here — two copies drift, and the one
      // in the browser is the one nobody re-checks.
      setError(err)
      setBusy(false)
    }
  }

  if (!open) return null

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const errorOn = (field) => (error && error.field === field ? error.message : null)

  // PORTALLED to <body>. `inert` applies to a subtree, so a dialog rendered
  // inside `.app` would make itself inert the moment it asked for the
  // background to be.
  return createPortal(
    <div className="scrim" onMouseDown={(e) => e.target === e.currentTarget && tryClose()}>
      <div
        className="panel"
        data-lenis-prevent=""
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-title`}
        data-testid="expense-panel"
        onKeyDown={onKeyDown}
      >
        <h2 className="panel-title" id={`${id}-title`}>
          {editing ? 'Edit expense' : 'Add an expense'}
        </h2>

        {error && !error.field && (
          <p className="form-error" role="alert" data-testid="panel-error">{error.message}</p>
        )}

        <form onSubmit={submit} noValidate>
          <div className="field field-amount">
            <label htmlFor={`${id}-amount`}>Amount</label>
            {/* The dollar sign is drawn beside the figure, not typed into it:
                the field's value stays the plain decimal the server parses. */}
            <div className="amount-wrap">
              <span className="amount-cur" aria-hidden="true">$</span>
              <input
                id={`${id}-amount`}
                name="amount"
                className="sw-num"
                inputMode="decimal"
                // Two decimal places, enforced in the field (`SW-ADR-112`), so
                // the server's 422 is a backstop the person should never meet.
                // The server still checks — this is courtesy, not the rule.
                pattern="^[0-9]{1,15}(\.[0-9]{1,2})?$"
                placeholder="0.00"
                autoComplete="off"
                value={form.amount}
                onChange={set('amount')}
                aria-invalid={errorOn('amount') ? 'true' : undefined}
                aria-describedby={errorOn('amount') ? `${id}-amount-err` : undefined}
                required
              />
            </div>
            {errorOn('amount') && (
              <span className="field-error" id={`${id}-amount-err`} role="alert">
                {errorOn('amount')}
              </span>
            )}
          </div>

          <div className="field-pair">
            <div className="field">
              <label htmlFor={`${id}-date`}>Date</label>
              <DatePicker
                id={`${id}-date`}
                name="spent_on"
                value={form.spent_on}
                onChange={set('spent_on')}
                invalid={errorOn('spent_on')}
                describedBy={errorOn('spent_on') ? `${id}-date-err` : undefined}
                required
              />
              {errorOn('spent_on') && (
                <span className="field-error" id={`${id}-date-err`} role="alert">{errorOn('spent_on')}</span>
              )}
            </div>

            <div className="field">
              <label htmlFor={`${id}-category`}>Category</label>
              <select
                id={`${id}-category`}
                name="category_id"
                value={form.category_id}
                onChange={set('category_id')}
                aria-invalid={errorOn('category_id') ? 'true' : undefined}
                aria-describedby={errorOn('category_id') ? `${id}-category-err` : undefined}
              >
                <option value="">No category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              {errorOn('category_id') && (
                <span className="field-error" id={`${id}-category-err`} role="alert">{errorOn('category_id')}</span>
              )}
            </div>
          </div>

          <div className="field">
            <label htmlFor={`${id}-description`}>Note <span className="entry-meta">(optional)</span></label>
            <input
              id={`${id}-description`}
              name="description"
              maxLength={500}
              value={form.description}
              onChange={set('description')}
              aria-invalid={errorOn('description') ? 'true' : undefined}
              aria-describedby={errorOn('description') ? `${id}-description-err` : undefined}
            />
            {errorOn('description') && (
              <span className="field-error" id={`${id}-description-err`} role="alert">{errorOn('description')}</span>
            )}
          </div>

          <div className="panel-actions">
            <button type="button" className="btn btn-quiet" onClick={tryClose}>
              Cancel
            </button>
            {/* `aria-disabled` plus a guard, not the `disabled` attribute: a
                disabled button drops out of the tab order mid-interaction, so
                a keyboard user's focus lands on <body> the moment they submit.
                The guard in `submit` is what actually prevents the double. */}
            <button
              type="submit"
              className="btn"
              data-testid="panel-submit"
              aria-disabled={busy ? 'true' : undefined}
            >
              {busy ? 'Saving…' : editing ? 'Save changes' : 'Add expense'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body,
  )
}
