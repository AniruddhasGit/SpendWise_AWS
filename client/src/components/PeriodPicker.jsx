import { PERIODS, identify, today } from '../lib/period.js'

/**
 * The period chips. `SRC-001 §9.1` names three — this month, last month, last
 * 30 days — and `CR-001` adds last 90 days and this year. The list is not here:
 * it is `PERIODS`, so the admin pane's picker and this one cannot drift.
 *
 * The chips are `aria-pressed` toggles rather than a radio group, matching the
 * design system's chip spec (`§5`). When the URL carries a range that matches
 * none of them — a shared link, or a hand-edited query string — no chip is
 * pressed and the current range is named beside them, so the screen never
 * claims a period it is not showing.
 */
export default function PeriodPicker({ range, onChange, disabled }) {
  const now = today()
  const active = identify(range, now)

  return (
    <div className="periods" role="group" aria-label="Period">
      {PERIODS.map((p) => (
        <button
          key={p.id}
          type="button"
          className="chip"
          data-testid={`period-${p.id}`}
          aria-pressed={active === p.id}
          aria-disabled={disabled ? 'true' : undefined}
          onClick={() => !disabled && onChange(p.range(now))}
        >
          {p.label}
        </button>
      ))}
      {active === null && (
        <span className="chip" aria-pressed="true" data-testid="period-custom">
          {range.from} to {range.to}
        </span>
      )}
    </div>
  )
}
