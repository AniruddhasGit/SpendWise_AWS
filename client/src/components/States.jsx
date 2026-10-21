/**
 * The screen states of E3-S6. Four, and they are FOUR — the point of the story
 * is that they are distinguishable, so they are separate components rather
 * than one with a message prop.
 *
 * Each carries a small hand-drawn mark (24 viewBox, 1.75 stroke, currentColor,
 * aria-hidden) so the four read differently at a glance, not only by their
 * words: a blank receipt, an empty search, a broken line. No numbers appear in
 * any of them, because a figure here would be read as a real one.
 */

import MoneyTree from './MoneyTree.jsx'
import Fog from './Fog.jsx'

function Mark({ tone = 'gold', d }) {
  return (
    <span className={`state-mark state-mark-${tone}`} aria-hidden="true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
           strokeLinecap="round" strokeLinejoin="round">
        <path d={d} />
      </svg>
    </span>
  )
}

// A receipt with a torn foot: the ledger nobody has written in yet.
// A lens over nothing.
const SEARCH = 'M10.5 4.5a6 6 0 1 1 0 12 6 6 0 0 1 0-12zM15 15l4.5 4.5M8.5 10.5h4'
// A line that breaks.
const BROKEN = 'M4 14l4-4 3 3M13 11l2-2 5 5M12 4v3M12 17v3'

/** A brand-new account: no ribbon, no bars, ONE primary action. */
export function FirstRun({ onAdd }) {
  return (
    <div className="state state-first-run sw-enter" data-testid="state-first-run">
      {/* the tree carried in from the sign-in page (SW-ADR-160), bare of
          falling bills: nothing has been spent yet */}
      <div className="dash-tree first-run-tree">
        <Fog className="gate-fog gate-fog-back" layer="back" pool stage=".dash-tree" />
        <MoneyTree variant="dashboard" drops={false} alt="" />
        <Fog className="gate-fog gate-fog-front" pool stage=".dash-tree" />
      </div>
      <h2 className="state-title">Your ledger is empty</h2>
      <p className="state-body">
        Log what you spend and SpendWise shows you where it went, by category
        and by day, and what that averages to.
      </p>
      <button type="button" className="btn btn-lg" onClick={onAdd} data-testid="first-add">
        Add your first expense
      </button>
    </div>
  )
}

/**
 * A filter matching nothing. A DIFFERENT state from first-run, with a
 * clear-filter affordance — the two look identical if you write them as one
 * "empty" component, and then a person with a year of history is told they
 * have never spent anything.
 */
export function NoMatches({ label, onClear, onAdd }) {
  return (
    <div className="state state-no-matches sw-enter" data-testid="state-no-matches">
      <Mark tone="muted" d={SEARCH} />
      <h2 className="state-title">No spending in {label}</h2>
      <p className="state-body">
        {onClear
          ? 'There is nothing recorded for this filter. Your other entries are still there.'
          : 'Nothing was recorded in this period. Your other entries are still there.'}
      </p>
      {/* The affordance matches what is actually on: a period with nothing in
          it has no filter to clear, and offering to clear one that does not
          exist is a button that appears to do nothing. */}
      {onClear ? (
        <button type="button" className="btn btn-quiet" onClick={onClear}
                data-testid="clear-filter">
          Clear the filter
        </button>
      ) : (
        <button type="button" className="btn" onClick={onAdd} data-testid="add-here">
          Add an expense
        </button>
      )}
    </div>
  )
}

/**
 * A failed request. **Never renders 0.00** — E3-S6 AC3, and the sharpest rule
 * on this screen. A zero where a total should be is indistinguishable from
 * "you spent nothing", and it is the number a person acts on.
 *
 * Retry preserves the period, because the period is in the URL and this
 * component does not touch it.
 */
export function LoadFailed({ error, onRetry }) {
  return (
    <div className="state state-error" role="alert" data-testid="state-error">
      <Mark tone="danger" d={BROKEN} />
      <h2 className="state-title">Could not load your spending</h2>
      <p className="state-body">
        {error?.message || 'Something went wrong.'} Nothing has been changed.
      </p>
      <button type="button" className="btn" onClick={onRetry} data-testid="retry">
        Try again
      </button>
    </div>
  )
}

/**
 * Loading. Shaped like the screen it precedes (the statement card, then a few
 * ledger rows) so the layout does not jump, and, again, carrying no numbers at
 * all. It fades in after 150ms, so a fast answer never flashes a skeleton.
 */
export function Loading() {
  return (
    <div className="state-loading" data-testid="state-loading" aria-busy="true" aria-live="polite">
      <p className="visually-hidden">Loading your spending.</p>
      <div className="skeleton state-loading-card" />
      <div className="state-loading-rows">
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    </div>
  )
}
