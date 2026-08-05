import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api.js'
import { days, rupees } from '../lib/money.js'
import { labelFor, readCategory, readRange, writeState } from '../lib/period.js'
import DayBars from '../components/DayBars.jsx'
import EntryList from '../components/EntryList.jsx'
import ExpensePanel from '../components/ExpensePanel.jsx'
import PeriodPicker from '../components/PeriodPicker.jsx'
import Ribbon from '../components/Ribbon.jsx'
import { FirstRun, Loading, LoadFailed, NoMatches } from '../components/States.jsx'

const UNCATEGORISED_COLOR = 'var(--sw-cat-uncat)'

/**
 * The dashboard.
 *
 * **Two summaries, deliberately.** `SW-ADR-109`: selecting a band re-scopes
 * the total, count, average, day bars and list — but NOT the ribbon, which
 * stays whole-period so proportions stay visible and the other bands stay
 * reachable. One summary cannot serve both: filtering it would collapse the
 * ribbon to a single band, and the person would have no way back except a
 * control that is no longer on screen.
 *
 * So `whole` drives the ribbon and `scoped` drives everything else. When
 * nothing is filtered they are the same request and the second is skipped.
 */
export default function Dashboard({ principal, draft, onDraft, onSignOut }) {
  const [range, setRange] = useState(() => readRange())
  const [category, setCategory] = useState(() => readCategory())

  const [whole, setWhole] = useState(null)
  const [scoped, setScoped] = useState(null)
  const [entries, setEntries] = useState(null)
  const [categories, setCategories] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  // Has this account EVER recorded an expense — a different question from
  // "did it record one this month", and the difference between the first-run
  // state and the empty-period one. Asked with no date filter, so an empty
  // July never tells a person with a year of history that they have never
  // spent anything (E3-S6 AC1 vs AC2).
  const [everAny, setEverAny] = useState(null)
  // A ref as well as state, so `load` does not list `everAny` as a dependency
  // — it would be rebuilt the moment the answer arrived and fire a second
  // round of every request on first paint.
  const answered = useRef(false)

  const [panelOpen, setPanelOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [busyId, setBusyId] = useState(null)

  // `inert` while the panel is open — the design system asks for it by name.
  // Set as a PROPERTY rather than a JSX attribute: React 18 does not know the
  // `inert` attribute and stringifies `inert={false}` to `inert="false"`,
  // which is a present attribute and therefore true. Every browser this
  // targets supports the property.
  const shell = useRef(null)

  // Every load gets a sequence number and a stale response is dropped. Without
  // it, clicking through three periods quickly can land the FIRST response
  // last and show a month nobody asked for — a race that reproduces about one
  // time in twenty and is untraceable when it does.
  const loadSeq = useRef(0)

  // Back and Forward move between periods rather than out of the app
  // (E3-S2 AC3). The URL is the state; this listener re-reads it.
  useEffect(() => {
    const onPop = () => {
      setRange(readRange())
      setCategory(readCategory())
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  // Write the OPENING url without a history entry, so the first Back leaves
  // the app rather than going to a bare `/` that renders the same screen.
  useEffect(() => { writeState({ ...range, category }, { replace: true }) }, [])

  const load = useCallback(async () => {
    const seq = ++loadSeq.current
    setLoading(true)
    setError(null)
    try {
      const filter = category === 'none' ? { uncategorised: true }
                   : category ? { category_id: category }
                   : {}
      const [w, list, cats, ever] = await Promise.all([
        api.summary({ from: range.from, to: range.to }),
        api.expenses({ from: range.from, to: range.to, limit: 200,
                       ...(category === 'none' ? {} : category ? { category_id: category } : {}) }),
        api.categories(),
        // One row, no date filter — the cheapest way to ask "is this account
        // new". Skipped once the answer is yes, because it can never go back.
        answered.current ? Promise.resolve(null) : api.expenses({ limit: 1 }),
      ])
      // Only ask twice when a filter is actually on.
      const s = Object.keys(filter).length
        ? await api.summary({ from: range.from, to: range.to, ...filter })
        : w
      if (seq !== loadSeq.current) return
      setWhole(w)
      setScoped(s)
      // `uncategorised` has no equivalent on the list endpoint — the contract
      // gives `category_id` only — so that one case is filtered client-side
      // over a page that is already bounded by the period.
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
      // A 401 has already been routed by `api.js`; leaving it to render an
      // error panel would flash "could not load" behind the sign-in screen.
      if (err.status !== 401) setError(err)
    } finally {
      if (seq === loadSeq.current) setLoading(false)
    }
  }, [range.from, range.to, category])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (shell.current) shell.current.inert = panelOpen
  }, [panelOpen])

  const colours = useMemo(() => {
    const m = new Map()
    for (const c of categories) m.set(c.id, c.color)
    return m
  }, [categories])

  const colorFor = useCallback(
    (id) => (id === null || id === undefined ? UNCATEGORISED_COLOR : colours.get(id) || UNCATEGORISED_COLOR),
    [colours])

  const changeRange = (next) => {
    setRange(next)
    setCategory(null)          // a band from last month means nothing in this one
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
    // `SW-ADR-119`: a destructive action names its blast radius before it runs.
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

  const periodLabel = labelFor(range)
  // Whether the ACCOUNT is new, not whether this PERIOD is empty. The first
  // version asked `whole.count === 0`, and a browser test caught it: switching
  // to a month with no spending told person A — who has four expenses — that
  // they had never recorded one, and replaced their period picker's context
  // with "add your first expense".
  const accountIsNew = everAny === false

  return (
    <>
    {/* The panel is a SIBLING of the shell, not a descendant. `inert` applies
        to a subtree, so a panel inside the shell would make itself inert. */}
    <div className="shell" ref={shell}>
      <header className="topbar">
        <h1 className="wordmark">SpendWise</h1>
        <div className="whoami">
          <span data-testid="whoami">{principal.display_name}</span>
          <button type="button" className="btn-link" onClick={onSignOut} data-testid="sign-out">
            Sign out
          </button>
        </div>
      </header>

      <main id="main">
        <PeriodPicker range={range} onChange={changeRange} disabled={loading} />

        {error ? (
          <LoadFailed error={error} onRetry={load} />
        ) : loading && !whole ? (
          <Loading />
        ) : !whole ? null : accountIsNew ? (
          <FirstRun onAdd={openAdd} />
        ) : (
          <>
            <section className="headline" aria-live="polite" data-testid="headline">
              <p className="headline-label">
                {category !== null ? 'Filtered total' : 'Total'} · {periodLabel}
              </p>
              <p className="headline-total sw-num" data-testid="total">
                {rupees(scoped.total_paise)}
              </p>
              <div className="headline-facts">
                <div>
                  <span className="fact-label">Entries</span>
                  <span className="fact-value sw-num" data-testid="count">{scoped.count}</span>
                </div>
                <div>
                  <span className="fact-label">Days elapsed</span>
                  <span className="fact-value sw-num" data-testid="days-elapsed">
                    {days(scoped.days_elapsed)}
                  </span>
                </div>
                <div>
                  <span className="fact-label">Daily average</span>
                  {/* `null`, never 0.00, when no day has elapsed — a wholly
                      future range has no average, and 0.00 reads as "spent
                      nothing" on the first screen a new account sees
                      (`SW-ADR-053`). */}
                  <span className="fact-value sw-num" data-testid="daily-average">
                    {scoped.daily_average_paise === null
                      ? 'Not yet'
                      : rupees(scoped.daily_average_paise)}
                  </span>
                </div>
              </div>
            </section>

            {/* The RIBBON reads `whole`. Everything else reads `scoped`. */}
            <Ribbon buckets={whole.by_category} selected={category} onSelect={changeCategory} />

            <DayBars days={scoped.by_day} />

            <div className="section-head">
              <h2 className="section-title">Entries</h2>
              <button type="button" className="btn" onClick={openAdd} data-testid="add-expense">
                Add expense
              </button>
            </div>

            {entries && entries.items.length === 0 ? (
              <NoMatches
                label={category !== null ? 'this category' : periodLabel.toLowerCase()}
                onClear={category !== null ? () => changeCategory(null) : null}
                onAdd={openAdd}
              />
            ) : entries ? (
              <EntryList
                items={entries.items}
                colorFor={colorFor}
                onEdit={openEdit}
                onDelete={remove}
                busyId={busyId}
              />
            ) : null}
          </>
        )}
      </main>
    </div>

    <ExpensePanel
      open={panelOpen}
      editing={editing}
      categories={categories}
      draft={draft}
      onDraft={onDraft}
      onSubmit={submit}
      onClose={() => setPanelOpen(false)}
    />
    </>
  )
}
