import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api.js'
import { rupees } from '../lib/money.js'
import { monthOf, today } from '../lib/period.js'

/**
 * Categories — the eight seeded ones **and any others a person makes**.
 *
 * `P-REC-05` always allowed this; nothing had built the screen. The eight of
 * `SW-ADR-092` are not special here: they were created by the application at
 * registration through the same endpoint this form posts to, so they rename,
 * recolour and delete exactly like one made this morning.
 *
 * **Deleting a category NULLS its expenses; it never deletes them**
 * (`SRC-001 §7.2`). The confirm names the blast radius before it runs
 * (`SW-ADR-119`) — this screen knows the count because the summary tells it,
 * so the number in the sentence is the real one.
 */

// The palette offered by the swatch picker. Every value is a design-system
// token read from the stylesheet at render time, never a literal — so a colour
// re-tinted in `tokens.css` moves this picker on the next paint.
const SWATCH_TOKENS = [
  '--sw-cat-1', '--sw-cat-2', '--sw-cat-3', '--sw-cat-4', '--sw-cat-5',
  '--sw-cat-6', '--sw-cat-7', '--sw-cat-8', '--sw-cat-uncat',
]

function paletteFromStylesheet() {
  const style = getComputedStyle(document.documentElement)
  return SWATCH_TOKENS
    .map((t) => style.getPropertyValue(t).trim().toLowerCase())
    .filter((v) => /^#[0-9a-f]{6}$/.test(v))
}

export default function Categories() {
  const [rows, setRows] = useState(null)
  const [usage, setUsage] = useState({})
  const [error, setError] = useState(null)
  const [editingId, setEditingId] = useState(null)
  const [busy, setBusy] = useState(false)

  const palette = useMemo(paletteFromStylesheet, [])
  const [form, setForm] = useState({ name: '', color: '' })
  const nameInput = useRef(null)

  useEffect(() => {
    // The palette is read AFTER the theme attribute is on `<html>`, so a dark
    // reader gets the dark tints — the same nine names, re-tinted by
    // `SW-ADR-147` because five of them measure under 3:1 on a dark surface.
    if (!form.color && palette.length) setForm((f) => ({ ...f, color: palette[0] }))
  }, [palette])

  const load = async () => {
    setError(null)
    try {
      const [cats, summary] = await Promise.all([
        api.categories(),
        // The current month, purely to show usage. A category with spending in
        // it is one you want a count for before you delete it.
        api.summary(monthOf(today())),
      ])
      setRows(cats)
      setUsage(Object.fromEntries(
        summary.by_category.filter((b) => b.category_id !== null)
          .map((b) => [b.category_id, b])))
    } catch (err) {
      if (err.status !== 401) setError(err)
    }
  }

  useEffect(() => { load() }, [])

  const create = async (event) => {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await api.createCategory({ name: form.name.trim(), color: form.color })
      setForm({ name: '', color: palette[0] })
      nameInput.current?.focus()
      await load()
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  const save = async (row, patch) => {
    setError(null)
    try {
      await api.updateCategory(row.id, patch)
      setEditingId(null)
      await load()
    } catch (err) {
      setError(err)
    }
  }

  const remove = async (row) => {
    const used = usage[row.id]
    // `SW-ADR-119`: name the blast radius, with the real number, before the
    // destructive act — and say what actually happens to the money, because
    // "delete" without that sentence sounds like it takes the expenses too.
    const scope = used
      ? `${used.count} expense${used.count === 1 ? '' : 's'} worth ${rupees(used.total_paise)} this month`
      : 'no expenses this month'
    if (!window.confirm(
      `Delete "${row.name}"?\n\nIt currently has ${scope}. Those expenses are KEPT — ` +
      `they become Uncategorised. Only the label goes.`)) return
    setError(null)
    try {
      await api.deleteCategory(row.id)
      await load()
    } catch (err) {
      setError(err)
    }
  }

  if (rows === null) {
    return <p className="entry-meta" aria-live="polite">Loading your categories.</p>
  }

  return (
    <>
      <header className="page-head">
        <div>
          <h1 className="page-title">Categories</h1>
          <p className="entry-meta">
            The eight you started with, and any you add. Renaming or recolouring
            one never touches the money in it.
          </p>
        </div>
      </header>

      {error && !error.field && (
        <p className="form-error" role="alert" data-testid="category-error">
          {error.message}
        </p>
      )}

      <section className="card" aria-labelledby="new-category">
        <h2 className="card-heading" id="new-category">Add a category</h2>
        <form className="row-form" onSubmit={create}>
          <div className="field field-grow">
            <label htmlFor="cat-name">Name</label>
            <input id="cat-name" ref={nameInput} value={form.name} maxLength={50}
                   data-testid="new-category-name" required
                   aria-invalid={error?.field === 'name' ? 'true' : undefined}
                   onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
            {error?.field === 'name' && (
              <span className="field-error" role="alert">{error.message}</span>
            )}
          </div>

          <fieldset className="field swatches">
            <legend>Colour</legend>
            {palette.map((hex) => (
              <button
                key={hex}
                type="button"
                className="swatch"
                data-testid={`swatch-${hex.slice(1)}`}
                style={{ background: hex }}
                aria-pressed={form.color === hex}
                aria-label={`Colour ${hex}`}
                onClick={() => setForm((f) => ({ ...f, color: hex }))}
              />
            ))}
          </fieldset>

          <button type="submit" className="btn" data-testid="create-category"
                  aria-disabled={busy ? 'true' : undefined}>
            {busy ? 'Adding…' : 'Add'}
          </button>
        </form>
      </section>

      <ul className="cat-list" data-testid="category-list">
        {rows.map((row) => (
          <li key={row.id} className="cat-row" data-testid={`category-${row.id}`}>
            <span className="cat-dot" aria-hidden="true" style={{ background: row.color }} />

            {editingId === row.id ? (
              <CategoryEditor row={row} palette={palette} error={error}
                              onCancel={() => { setEditingId(null); setError(null) }}
                              onSave={(patch) => save(row, patch)} />
            ) : (
              <>
                <span className="cat-name">{row.name}</span>
                <span className="entry-meta cat-usage" data-testid={`usage-${row.id}`}>
                  {usage[row.id]
                    ? `${usage[row.id].count} this month · ${rupees(usage[row.id].total_paise)}`
                    : 'nothing this month'}
                </span>
                <span className="cat-actions">
                  <button type="button" className="icon-btn"
                          data-testid={`edit-category-${row.id}`}
                          onClick={() => { setError(null); setEditingId(row.id) }}>
                    Edit
                  </button>
                  <button type="button" className="icon-btn"
                          data-testid={`delete-category-${row.id}`}
                          onClick={() => remove(row)}>
                    Delete
                  </button>
                </span>
              </>
            )}
          </li>
        ))}
      </ul>
    </>
  )
}

function CategoryEditor({ row, palette, error, onSave, onCancel }) {
  const [name, setName] = useState(row.name)
  const [color, setColor] = useState(row.color)

  return (
    <form
      className="cat-editor"
      onSubmit={(e) => { e.preventDefault(); onSave({ name: name.trim(), color }) }}
    >
      <div className="field field-grow">
        <label htmlFor={`rename-${row.id}`} className="visually-hidden">Name</label>
        <input id={`rename-${row.id}`} value={name} maxLength={50} autoFocus
               data-testid={`rename-${row.id}`}
               aria-invalid={error?.field === 'name' ? 'true' : undefined}
               onChange={(e) => setName(e.target.value)} />
        {error?.field === 'name' && (
          <span className="field-error" role="alert">{error.message}</span>
        )}
      </div>

      <fieldset className="field swatches">
        <legend className="visually-hidden">Colour</legend>
        {/* The row's CURRENT colour is offered even when it is not in the
            palette — a category recoloured before a token was re-tinted would
            otherwise silently change colour on save. */}
        {[...new Set([row.color, ...palette])].map((hex) => (
          <button key={hex} type="button" className="swatch" style={{ background: hex }}
                  aria-pressed={color === hex} aria-label={`Colour ${hex}`}
                  data-testid={`recolour-${row.id}-${hex.slice(1)}`}
                  onClick={() => setColor(hex)} />
        ))}
      </fieldset>

      <button type="submit" className="btn" data-testid={`save-category-${row.id}`}>
        Save
      </button>
      <button type="button" className="btn btn-quiet" onClick={onCancel}>Cancel</button>
    </form>
  )
}
