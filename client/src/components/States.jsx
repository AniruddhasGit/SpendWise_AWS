/**
 * The screen states of E3-S6. Four, and they are FOUR — the point of the story
 * is that they are distinguishable, so they are separate components rather
 * than one with a message prop.
 */

/** A brand-new account: no ribbon, no bars, ONE primary action. */
export function FirstRun({ onAdd }) {
  return (
    <div className="state" data-testid="state-first-run">
      <h2 className="state-title">Nothing here yet</h2>
      <p className="state-body">
        Log what you spend and SpendWise will show you where it went — by
        category, by day, and what that averages to.
      </p>
      <button type="button" className="btn" onClick={onAdd} data-testid="first-add">
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
    <div className="state" data-testid="state-no-matches">
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
 * Loading. Shaped like the screen it precedes so the layout does not jump —
 * and, again, carrying no numbers at all.
 */
export function Loading() {
  return (
    <div data-testid="state-loading" aria-busy="true" aria-live="polite">
      <p className="visually-hidden">Loading your spending.</p>
      <div className="headline">
        <div className="skeleton" style={{ width: '40%', height: 'var(--sw-space-12)' }} />
      </div>
      <div className="skeleton" style={{ height: 'var(--sw-space-12)' }} />
    </div>
  )
}
