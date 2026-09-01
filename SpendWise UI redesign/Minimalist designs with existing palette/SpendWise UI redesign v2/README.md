# Handoff: SpendWise Swiss restyle (olive palette, unchanged)

## What this is

A third visual revision of the SpendWise client. Where the 2026-08-21 handoff
changed the **palette** (paper-and-pine → olive / greenish-white / near-black),
this one changes the **surface language** and leaves every colour exactly where
it is.

The reference is Swiss / International-style: hairline rules instead of cards,
no shadows, no rounded corners, no page wash, oversized display type at tight
negative tracking, and a monospace uppercase micro-label on every label,
control and status in the app.

**Layout, markup, copy and behaviour are unchanged. No `.jsx` file should be
edited.** Every change is CSS on a class name that already exists.

## Files in this bundle

| File | What it is |
|---|---|
| `README.md` | this document |
| `docs-design-system-tokens.css` | **drop-in.** Replaces `docs/05 B DesignSystem/tokens.css` |
| `app.swiss.css` | **drop-in.** New `client/src/styles/app.swiss.css` |
| `SpendWise Swiss.dc.html` | **reference only.** Standalone prototype of all seven screens, both themes, with working nav, filters, theme toggle and panel. Do not copy into `client/` |

The prototype needs `support.js` beside it to run; read it as a spec, or open it
in the design tool it came from.

## Implementation

Two steps.

### 1. Replace the token source, then regenerate

```
SpendWise UI redesign v2/docs-design-system-tokens.css
  →  docs/05 B DesignSystem/tokens.css

py client/sync_tokens.py
```

`client/src/styles/tokens.css` carries a `GENERATED — do not edit` header.
Never hand-edit the client copy.

### 2. Add the restyle layer

```
SpendWise UI redesign v2/app.swiss.css
  →  client/src/styles/app.swiss.css
```

Import it **last** in `client/src/main.jsx`:

```js
import './styles/tokens.css'
import './styles/app.css'
import './styles/app.redesign.css'   // keep or drop — app.swiss.css overrides it either way
import './styles/app.swiss.css'      // ← add
```

It targets existing class names only, contains no raw hex, no `:focus-visible`
rule and no `outline: none`, so `lint:tokens` still passes.

## What changed in the tokens

**No colour moved.** Every hex in `docs-design-system-tokens.css` — including
all nine category bands, `--sw-warning` and `--sw-danger` — is byte-identical to
the value already in `client/src/styles/tokens.css`. `tools/contrast.py` figures
carry over unchanged, with one improvement: the glass alphas go to 1, so every
composited pair becomes its own unblended pair, which can only measure higher.

| Token | Was | Now | Why |
|---|---|---|---|
| `--sw-radius-sm` | `5px` | `0px` | a Swiss grid separates with rules, not corners |
| `--sw-radius-md` | `10px` | `0px` | |
| `--sw-radius-lg` | `14px` | `0px` | |
| `--sw-radius-full` | `999px` | *unchanged* | the three status dots legitimately want a circle; `app.swiss.css` squares the rest by name |
| `--sw-shadow-sm` | `0 1px 2px …` | `none` | separation is a 1px `--sw-border` hairline |
| `--sw-shadow-md` | `0 3px 14px …` | `none` | |
| `--sw-shadow-panel` | two-layer | `-1px 0 0 var(--sw-ink)` | the drawer keeps one hard edge |
| `--sw-text-2xl` | `2.5rem` | `4.25rem` | page titles |
| `--sw-text-3xl` | `3.75rem` | `5.75rem` | the hero total |
| `--sw-leading-tight` | `1.08` | `0.9` | display type sets tight |
| `--sw-glass` | `rgb(251 252 246 / .80)` | `var(--sw-paper)` | opaque; a ruled grid needs a flat ground |
| `--sw-glass-strong` | `rgb(… / .93)` | `var(--sw-paper)` | |
| `--sw-glass-sunken` | `rgb(… / .70)` | `var(--sw-paper-sunken)` | |
| `--sw-glass-border` | `rgb(255 255 255 / .62)` | `var(--sw-border)` | the highlight becomes a hairline |
| `--sw-glass-blur` | `16px` | `0px` | |
| `--sw-wash-1` / `-2` | olive radials | `transparent` | the page is flat paper |
| `--sw-plot-fill` | `… / 0.15` | `… / 0.10` | quieter area under the line |
| `--sw-plot-grid` | `… / 0.07` | `… / 0.09` | the gridline is now the only chart furniture, so it reads |

Token **names** are unchanged. `--sw-pine` still means "the accent".

## The idiom, in four rules

1. **Labels are mono, uppercase, wide-tracked, 10px.** `.card-label`,
   `.card-heading`, `.ribbon-title`, `.rail-heading`, `.facts dt`,
   `.table thead th`, `.field label`, `.swatches legend`. The four heading-ish
   ones take a `::before` `//` marker — that is the one visual device of the
   reference that would otherwise need markup, and `::before` gets it with no
   `.jsx` change.
2. **Titles are display grotesque, 700, uppercase, `-0.045em`.** `.page-title`,
   `.gate-title`. `.section-title` and `.state-title` the same at `2.125rem`.
   The accent rule under `.page-title` (`::after`) is removed; the title sits on
   a full-width `--sw-ink` hairline instead.
3. **Numbers are mono tabular at negative tracking.** The hero total at
   `--sw-text-3xl`/`-0.05em`, stat values at `2.125rem`, entry amounts and table
   figures at body size. `.sw-num` still carries `tnum` — do not remove it.
4. **Nothing is separated by a shadow or a corner.** Cards become grid cells
   with `box-shadow: inset 1px 0 0 var(--sw-border)`; lists, tables, legends,
   bar rows and entries are divided by `1px solid var(--sw-border)`; section
   boundaries that matter use `--sw-ink`.

### One trap worth naming

The card dividers are an **inset shadow on each cell**, not a background on the
grid container. `gap: 1px; background: var(--sw-border)` looks equivalent and is
not: `.cards` is `repeat(auto-fit, minmax(13rem, 1fr))` and three stat cards in
two columns leave one cell empty, where the container's background shows through
as a solid olive block. The inset rule draws only where a real cell is, in both
the stacked and unstacked state. Do not "simplify" it back.

Likewise the auto-fit floors (`13rem` on `.cards`, `20rem` on `.panels`) stay.
Pinning them to a fixed column count squeezes cells below the width a mono
tabular figure needs, and a lakh figure clips.

## Per-class inventory

`app.swiss.css` is sectioned and commented; the headings are:

1. the page (flat `--sw-paper`)
2. flattening the glass surface list
3. the mono micro-label idiom, and `::placeholder`
4. titles
5. the hero total
6. cards as grid cells
7. the rail
8. content column
9. buttons
10. chips and the segmented control
11. admin tabs (underline on a rule)
12. charts (donut, legend, bars, daybars)
13. the ribbon — **surface only**
14. entries
15. categories
16. inputs (a ruled line, not a box)
17. the panel
18. tables
19. leaving
20. the gate
21. states, banners, skeletons
22. keyframes
23. phone width

## What is deliberately NOT changed

- **Any `.jsx` file.** If you find yourself editing one, the change belongs in
  CSS.
- **Token names.** `--sw-pine` is referenced across `app.css`, the docs and
  several ADRs.
- **Every colour value**, including the nine category bands, `--sw-warning` and
  `--sw-danger`.
- **The ribbon's proportional geometry** (`SW-ADR-055`) — no `min-width`, no
  `flex-grow`, no `gap` is added or removed. Section 12 changes only height,
  radius and ground. Both selection cues are kept: the chosen band gains the
  inset marker *and* the others dim to `0.35`.
- **The roving tabindex**, one Tab stop for the whole ribbon, `←`/`→`/`Home`/
  `End`/`Enter`/`Space`/`Escape`.
- **The two-summary rule** (`SW-ADR-109`): the ribbon and the donut stay
  whole-period.
- **The dialog's focus trap**, `inert` handling, document-level Escape, and the
  absence of an optimistic insert.
- **The single `:focus-visible` rule** and its location in `tokens.css`.
- **`--sw-ink-faint` never carries content** (`SW-ADR-117`). In this layer it
  appears exactly twice: the `//` marker glyph and `::placeholder`. Everything a
  person has to read is `--sw-ink-muted` or darker.
- **The absence of a router.**
- Phone width: single column below 900px, panel from the bottom, ribbon scrolls,
  two lines per entry, 44px floor on every control.

## Fonts

Unchanged, and still the one item needing real work: there is no `@font-face`
rule and no font file under `client/`, so the app renders `system-ui` and
`ui-monospace` fallbacks. This restyle leans much harder on the mono than the
last one did — **JetBrains Mono is now carrying every label in the app** — so
self-hosting it matters more than before.

`SW-ADR-020` rejects a font CDN. Fetch the woff2 files (all three families are
SIL OFL), put them in `client/public/fonts/`, and add to `app.swiss.css`:

```css
@font-face { font-family: "Bricolage Grotesque";
             src: url("/fonts/BricolageGrotesque.woff2") format("woff2");
             font-weight: 400 700; font-display: swap; }
@font-face { font-family: "DM Sans";
             src: url("/fonts/DMSans.woff2") format("woff2");
             font-weight: 400 700; font-display: swap; }
@font-face { font-family: "JetBrains Mono";
             src: url("/fonts/JetBrainsMono.woff2") format("woff2");
             font-weight: 400 600; font-display: swap; }
```

Note `600` on the mono — the label idiom uses semibold.

## Verification — required before merge

```
py tools/contrast.py
npm run lint:tokens
py -m pytest tests/browser
```

`contrast.py` should come back clean or better than the last run: no colour
moved, and the translucent surfaces became opaque. The pairs to read anyway,
because the *geometry* around them changed:

- `--sw-border` `#d8e0c2` vs `--sw-paper` — it is now the only separator in the
  app, so it is doing structural work a 1px hairline has to be visible for. It
  is decoration, not a UI component boundary a person operates, so it has no
  3:1 floor — but if it reads as absent on a low-quality panel, darken toward
  `--sw-border-strong` rather than adding a shadow back.
- `--sw-ink-muted` `#4f5643` at 10px — the label size dropped, and WCAG's 4.5:1
  floor does not bend for small text. `#4f5643` on paper clears it; do not
  substitute `--sw-ink-faint` anywhere in this layer.
- `--sw-on-pine` on `--sw-pine` — unchanged, but every primary button is now
  10-12px mono, so the figure matters more.

`tests/browser` is the one that catches a restyle breaking behaviour: the 44px
floor at phone width, the ribbon's band widths, the focus trap, the theme
radiogroup.

## Documentation to update

- `docs/05 B DesignSystem/DESIGN-SYSTEM.md` — §2 (radius, shadow, glass rows),
  §3 (the two display steps and `--sw-leading-tight`), and the surface language
  description. §1's palette brief and the colour table are unaffected.
- `docs/05 B DesignSystem/CONTRAST.md` — regenerated by the tool.
- A **superseding ADR** recording the surface change, pointing at `SW-ADR-147`
  (glass) and the 2026-08-21 palette ADR, since this revision retires glass
  without retiring the palette. Add it to
  `docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv`.
