import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api.js'
import { days, rupees } from '../lib/money.js'
import { labelFor, previousMonthOf, readCategory, readRange, writeState } from '../lib/period.js'
import Bars from '../components/charts/Bars.jsx'
import Donut from '../components/charts/Donut.jsx'
import LinePlot from '../components/charts/LinePlot.jsx'
import EntryList from '../components/EntryList.jsx'
import ExpensePanel from '../components/ExpensePanel.jsx'
import PeriodPicker from '../components/PeriodPicker.jsx'
import Ribbon from '../components/Ribbon.jsx'
import { FirstRun, Loading, LoadFailed, NoMatches } from '../components/States.jsx'

const UNCATEGORISED_COLOR = 'var(--sw-cat-uncat)'
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

/**
 * The dashboard.
 *
 * **Two summaries, deliberately.** `SW-ADR-109`: selecting a category
 * re-scopes the total, count, average, plots and list — but NOT the ribbon or
 * the donut, which stay whole-period so proportions remain visible and the
 * other categories stay reachable. One summary cannot serve both: filtering it
 * would collapse the chart to a single slice, and the person would have no way
 * back except a control that is no longer on screen.
 *
 * So `whole` drives the two charts-that-are-also-filters, and `scoped` drives
 * everything else. When nothing is filtered they are the same request and the
 * second is skipped.
 *
 * A THIRD request fetches last month, because "up 12% on last month" is the
 * sentence people actually want and it cannot be computed from one range.
 */
export default function Dashboard({ principal, draft, onDraft }) {
  const [range, setRange] = useState(() => readRange())
  const [category, setCategory] = useState(() => readCategory())

  const [whole, setWhole] = useState(null)
  const [scoped, setScoped] = useState(null)
  const [previous, setPrevious] = useState(null)
  const [entries, setEntries] = useState(null)
  const [categories, setCategories] = useState([])
  const [everAny, setEverAny] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const [panelOpen, setPanelOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [busyId, setBusyId] = useState(null)

  const answered = useRef(false)
  const loadSeq = useRef(0)

  useEffect(() => {
    const onPop = () => { setRange(readRange()); setCategory(readCategory()) }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  useEffect(() => { writeState({ ...range, category }, { replace: true }) }, [])

  const load = useCallback(async () => {
    const seq = ++loadSeq.current
    setLoading(true)
    setError(null)
    try {
      const filter = category === 'none' ? { uncategorised: true }
                   : category ? { category_id: category } : {}
      const last = previousMonthOf(range.from)

      const [w, list, cats, ever, prev] = await Promise.all([
        api.summary({ from: range.from, to: range.to }),
        api.expenses({ from: range.from, to: range.to, limit: 200,
                       ...(category === 'none' ? {} : category ? { category_id: category } : {}) }),
        api.categories(),
        answered.current ? Promise.resolve(null) : api.expenses({ limit: 1 }),
        api.summary({ from: last.from, to: last.to }),
      ])
      const s = Object.keys(filter).length
        ? await api.summary({ from: range.from, to: range.to, ...filter })
        : w
      if (seq !== loadSeq.current) return

      setWhole(w)
      setScoped(s)
      setPrevious(prev)
      // `uncategorised` has no equivalent on the list endpoint — the contract
      // gives `category_id` only — so that one case is filtered client-side
      // over a page already bounded by the period.
      setEntries(category === 'none'
        ? { ...list, items: list.items.filter((e) => e.category_id === null) }
        : list)
      setCategories(cats)
      if (ever) {
        if (ever.total > 0) answered.current = true
        setEverAny(ever.total > 0)
      }
    } catch (err) {
      if (seq !== loadSeq.current) return
      if (err.status !== 401) setError(err)
    } finally {
      if (seq === loadSeq.current) setLoading(false)
    }
  }, [range.from, range.to, category])

  useEffect(() => { load() }, [load])

  const colours = useMemo(() => new Map(categories.map((c) => [c.id, c.color])), [categories])
  const colorFor = useCallback(
    (id) => (id == null ? UNCATEGORISED_COLOR : colours.get(id) || UNCATEGORISED_COLOR),
    [colours])

  const changeRange = (next) => {
    setRange(next)
    setCategory(null)                 // a category from last month means nothing here
    writeState({ ...next, category: null })
  }
  const changeCategory = (next) => {
    setCategory(next)
    writeState({ ...range, category: next })
  }

  const submit = async (body) => {
    if (editing) await api.updateExpense(editing.id, body)
    else await api.createExpense(body)
    // Reload AFTER the server confirms. The list never shows a row the server
    // has not accepted (E3-S5 AC5).
    await load()
  }

  const remove = async (expense) => {
    if (!window.confirm(`Delete ${rupees(expense.amount_paise)}? This cannot be undone.`)) return
    setBusyId(expense.id)
    try {
      await api.deleteExpense(expense.id)
      await load()
    } catch (err) {
      if (err.status !== 401) setError(err)
    } finally {
      setBusyId(null)
    }
  }

  const openAdd = () => { setEditing(null); setPanelOpen(true) }
  const openEdit = (e) => { setEditing(e); setPanelOpen(true) }

  // ── derived ──────────────────────────────────────────────────────────────
  const periodLabel = labelFor(range)
  const accountIsNew = everAny === false

  const delta = useMemo(() => {
    if (!scoped || !previous || previous.total_paise === 0) return null
    // Half-up in integers, exactly as the server rounds money. `Math.round` is
    // half-away-from-zero and would disagree by one on a value like 12.5%.
    const diff = scoped.total_paise - previous.total_paise
    const pct = Math.trunc((2 * Math.abs(diff) * 100 + previous.total_paise)
                           / (2 * previous.total_paise))
    return { diff, pct, up: diff > 0 }
  }, [scoped, previous])

  const projection = useMemo(() => {
    if (!scoped || scoped.daily_average_paise === null) return null
    const span = scoped.by_day.length
    if (span <= scoped.days_elapsed) return null   // the period has ended
    return scoped.daily_average_paise * span
  }, [scoped])

  const byWeekday = useMemo(() => {
    if (!scoped) return []
    const sums = new Array(7).fill(0)
    for (const d of scoped.by_day) {
      // Split the STRING and build a UTC date from the parts. `new Date(iso)`
      // parses as UTC midnight and reports the previous weekday west of
      // Greenwich — the same trap `money.js` documents.
      const [y, m, dd] = d.date.split('-').map(Number)
      sums[new Date(Date.UTC(y, m - 1, dd)).getUTCDay()] += d.total_paise
    }
    return WEEKDAYS.map((label, i) => ({ label, value: sums[i] }))
  }, [scoped])

  const biggest = useMemo(
    () => (entries?.items?.length
      ? entries.items.reduce((a, b) => (b.amount_paise > a.amount_paise ? b : a))
      : null),
    [entries])

  const daysLogged = useMemo(() => {
    if (!scoped) return null
    return {
      withSpending: scoped.by_day.filter((d) => d.total_paise > 0).length,
      of: scoped.days_elapsed,
    }
  }, [scoped])

  return (
    <>
      <div className="pane">
        <header className="page-head">
          <div>
            <h1 className="page-title">Your spending</h1>
            <p className="entry-meta" data-testid="period-label">
              {periodLabel} · {range.from} to {range.to}
            </p>
          </div>
          <button type="button" className="btn" onClick={openAdd} data-testid="add-expense">
            Add expense
          </button>
        </header>

        <PeriodPicker range={range} onChange={changeRange} disabled={loading} />

        {error ? (
          <LoadFailed error={error} onRetry={load} />
        ) : loading && !whole ? (
          <Loading />
        ) : !whole ? null : accountIsNew ? (
          <FirstRun onAdd={openAdd} />
        ) : (
          <>
            {/* The hero is its OWN full-width row, not a two-column span in
                the stat grid. Spanning clipped `₹3,790.49` at four columns —
                and a lakh figure is four characters longer, so the version
                that fitted today would not have fitted a real month. */}
            <section aria-label="Total">
              <article className="card card-hero" data-testid="headline">
                <p className="card-label">
                  {category !== null ? 'Filtered total' : 'Total'}
                </p>
                <p className="card-hero-value sw-num" data-testid="total">
                  {rupees(scoped.total_paise)}
                </p>
                {delta && (
                  <p className={`delta${delta.up ? ' is-up' : ' is-down'}`}
                     data-testid="delta">
                    {delta.up ? '▲' : '▼'} {delta.pct}%{' '}
                    <span className="entry-meta">
                      {delta.up ? 'more' : 'less'} than last month
                    </span>
                  </p>
                )}
              </article>
            </section>

            <section className="cards" aria-label="Headline figures">
              <article className="card">
                <p className="card-label">Entries</p>
                <p className="card-value sw-num" data-testid="count">{scoped.count}</p>
                {biggest && (
                  <p className="entry-meta" data-testid="biggest">
                    Largest {rupees(biggest.amount_paise)}
                  </p>
                )}
              </article>

              <article className="card">
                <p className="card-label">Daily average</p>
                {/* `null`, never 0.00, when no day has elapsed — a wholly
                    future range has no average, and 0.00 reads as "spent
                    nothing" on the first screen a new account sees
                    (`SW-ADR-053`). */}
                <p className="card-value sw-num" data-testid="daily-average">
                  {scoped.daily_average_paise === null
                    ? 'Not yet' : rupees(scoped.daily_average_paise)}
                </p>
                <p className="entry-meta" data-testid="days-elapsed">
                  over {days(scoped.days_elapsed)}
                </p>
              </article>

              <article className="card">
                <p className="card-label">On track for</p>
                <p className="card-value sw-num" data-testid="projection">
                  {projection === null ? '—' : rupees(projection)}
                </p>
                <p className="entry-meta">
                  {projection === null
                    ? 'this period has finished'
                    : 'estimate, if the rest matches so far'}
                </p>
              </article>
            </section>

            <section className="panels" aria-label="Charts">
              <article className="card">
                <h2 className="card-heading">Spending over time</h2>
                <LinePlot days={scoped.by_day} />
              </article>

              <article className="card">
                <h2 className="card-heading">By category</h2>
                {/* Reads `whole`, never `scoped` — see the note at the top. */}
                <Donut buckets={whole.by_category} selected={category}
                       onSelect={changeCategory} total={scoped.total_paise} />
              </article>
            </section>

            {/* The same filter in a different shape, and the one that stays
                proportion-true at any width (`SW-ADR-055`). Both write the same
                state, so they cannot disagree. */}
            <Ribbon buckets={whole.by_category} selected={category}
                    onSelect={changeCategory} />

            <section className="panels" aria-label="Patterns">
              <article className="card">
                <h2 className="card-heading">Running total</h2>
                <LinePlot days={scoped.by_day} cumulative height={140} />
              </article>

              <article className="card">
                <h2 className="card-heading">By day of the week</h2>
                <Bars rows={byWeekday} testId="weekday-bars"
                      label="Spending by day of the week" />
                {daysLogged && (
                  <p className="entry-meta" data-testid="days-logged">
                    Recorded on {daysLogged.withSpending} of {days(daysLogged.of)}.
                  </p>
                )}
              </article>
            </section>

            <div className="section-head">
              <h2 className="section-title">Entries</h2>
              {category !== null && (
                <button type="button" className="btn-link"
                        onClick={() => changeCategory(null)} data-testid="clear-filter-top">
                  Clear filter
                </button>
              )}
            </div>

            {entries && entries.items.length === 0 ? (
              <NoMatches
                label={category !== null ? 'this category' : periodLabel.toLowerCase()}
                onClear={category !== null ? () => changeCategory(null) : null}
                onAdd={openAdd}
              />
            ) : entries ? (
              <EntryList items={entries.items} colorFor={colorFor}
                         onEdit={openEdit} onDelete={remove} busyId={busyId} />
            ) : null}
          </>
        )}
      </div>

      <ExpensePanel
        open={panelOpen} editing={editing} categories={categories}
        draft={draft} onDraft={onDraft} onSubmit={submit}
        onClose={() => setPanelOpen(false)}
      />
    </>
  )
}
