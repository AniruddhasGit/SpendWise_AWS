# Handoff: SpendWise UI redesign (olive / greenish-white / near-black)

## Overview

SpendWise is a personal expense tracker: a FastAPI backend and a React + Vite
client at `client/`, with a documented design system at
`docs/05 B DesignSystem/`. The visual identity is being changed from
**paper-and-pine** (warm off-white + forest green + Instrument Serif) to
**greenish-white / olive / near-black** with a new type pairing.

**Layout, markup, copy and behaviour are unchanged.** The client asked to
"keep everything the same" and only re-skin. This is a theming change, and the
codebase was built so that a theming change is a theming change: every colour,
font, radius, shadow and duration is a CSS custom property in one generated
file, and `npm run lint:tokens` fails the build if any component declares a raw
hex. **No `.jsx` file should be edited.**

## About the design files

`SpendWise.dc.html` in this bundle is a **design reference created in HTML** —
a standalone prototype of all seven screens with working navigation, filters,
theme toggle and the add-expense panel. It is *not* production code and must
not be copied into `client/`. Its purpose is to show the intended look and to
let you compare against your build.

The two CSS files in this bundle, by contrast, **are** intended for the
codebase. They are written against the existing class names and token names and
are meant to be dropped in as described under *Implementation*.

## Fidelity

**High-fidelity.** Exact hex values, font stacks, radii, shadows and durations
are specified below and in the CSS files. Recreate the result pixel-accurately.

## Target codebase

| | |
|---|---|
| Client | React 18 + Vite, `client/` |
| Entry | `client/src/main.jsx` → `App.jsx` |
| Styles | `client/src/styles/tokens.css` (generated), `client/src/styles/app.css` |
| Token source of truth | `docs/05 B DesignSystem/tokens.css` |
| Regenerate command | `py client/sync_tokens.py` |
| Guard | `npm run lint:tokens`, `py tools/contrast.py`, `pytest tests/browser` |
| Screens | `client/src/screens/{Gate,Dashboard,Categories,Settings,Admin}.jsx` |
| Shell | `client/src/App.jsx`, `client/src/components/Sidebar.jsx` |

There is deliberately **no router** — the panes are application state, not
addresses (`SRC-001 §12.1`). Do not add one.

## Implementation

Three steps. Nothing else.

### 1. Replace the token source, then regenerate

```
design_handoff_spendwise_redesign/docs-design-system-tokens.css
  →  docs/05 B DesignSystem/tokens.css

py client/sync_tokens.py
```

`client/src/styles/tokens.css` carries a `GENERATED — do not edit` header and
`py client/sync_tokens.py --check` compares it against the docs copy. Never
hand-edit the client copy.

The **token names are unchanged.** `--sw-pine` still means "the accent"; it now
holds an olive. This is why no component needs touching. Do not rename it — it
is referenced across `app.css`, `DESIGN-SYSTEM.md` and several ADRs.

### 2. Add the redesign layer

```
design_handoff_spendwise_redesign/app.redesign.css
  →  client/src/styles/app.redesign.css
```

Import it **after** `app.css` in `client/src/main.jsx`:

```js
import './styles/tokens.css'
import './styles/app.css'
import './styles/app.redesign.css'   // ← add
```

It targets existing class names only and invents no class a `.jsx` file would
have to learn. It contains no raw hex, no `:focus-visible` rule and no
`outline: none`, so `lint:tokens` still passes.

### 3. One meta tag

`client/index.html` pins `<meta name="color-scheme" content="light">`, which
makes the browser paint native form controls and scrollbars light even under
the dark theme:

```html
<meta name="color-scheme" content="light dark" />
```

## Design tokens

All values below are the light theme unless the dark column is given. Category
band colours are **unchanged** in both themes.

### Colour — light

| Token | New | Old | Role |
|---|---|---|---|
| `--sw-paper` | `#f2f5e9` | `#faf7f2` | the page. Greenish white, never pure white |
| `--sw-paper-raised` | `#fbfcf6` | `#ffffff` | cards, the add-expense panel |
| `--sw-paper-sunken` | `#eaefdc` | `#f0ece4` | table headers, inset wells |
| `--sw-ink` | `#14170e` | `#1c1917` | primary text. Near-black, never `#000` |
| `--sw-ink-muted` | `#4f5643` | `#57534e` | secondary text, labels, timestamps |
| `--sw-ink-faint` | `#7c8468` | `#78716c` | placeholder/disabled ONLY — never content |
| `--sw-pine` | `#4e5f22` | `#2d5a3d` | **the accent.** Primary buttons, active states, links |
| `--sw-pine-deep` | `#354115` | `#1b3826` | pressed and hover on the accent |
| `--sw-pine-soft` | `#e2eaca` | `#e6ede8` | tinted backgrounds behind accent content |
| `--sw-border` | `#d8e0c2` | `#ddd6cb` | hairlines, input borders |
| `--sw-border-strong` | `#7f8a63` | `#8a837b` | table rules, focus-adjacent borders |
| `--sw-positive` | `#4e5f22` | `#2d5a3d` | same as the accent |
| `--sw-warning` | `#8a5a1f` | *unchanged* | approaching a limit |
| `--sw-danger` | `#9c2f28` | *unchanged* | destructive actions, validation errors |
| `--sw-on-pine` | `#f7faee` | `#faf7f2` | text on an accent or danger fill |
| `--sw-plot-line` | `#4e5f22` | `#2d5a3d` | chart stroke |
| `--sw-plot-fill` | `rgb(78 95 34 / 0.15)` | | chart area fill |
| `--sw-plot-grid` | `rgb(20 23 14 / 0.07)` | | chart gridlines |
| `--sw-scrim` | `rgb(20 23 14 / 0.38)` | | the dialog backdrop |
| `--sw-glass` | `rgb(251 252 246 / 0.80)` | | cards, rail, panels |
| `--sw-glass-strong` | `rgb(251 252 246 / 0.93)` | | anything over content |
| `--sw-glass-sunken` | `rgb(234 239 220 / 0.70)` | | wells, table headers |
| `--sw-glass-border` | `rgb(255 255 255 / 0.62)` | | the 1px glass highlight |
| `--sw-wash-1` | `rgb(78 95 34 / 0.13)` | | page wash radial 1 (olive) |
| `--sw-wash-2` | `rgb(20 23 14 / 0.05)` | | page wash radial 2 |

`--sw-glass-blur` stays `16px`. `backdrop-filter` remains progressive
enhancement — every surface is opaque enough to clear its floor without it.

### Colour — dark

Dark is not an inversion (`SW-ADR-147`). Olive `#4e5f22` measures far under 3:1
on a near-black ground, so dark uses a light tint of the same hue.

| Token | Value |
|---|---|
| `--sw-paper` | `#0d0f09` |
| `--sw-paper-raised` | `#181c10` |
| `--sw-paper-sunken` | `#0a0c06` |
| `--sw-ink` | `#eef2e2` |
| `--sw-ink-muted` | `#a8b096` |
| `--sw-ink-faint` | `#79806a` |
| `--sw-pine` | `#b8d16b` |
| `--sw-pine-deep` | `#d0e28a` |
| `--sw-pine-soft` | `#1f2612` |
| `--sw-border` | `#2a3019` |
| `--sw-border-strong` | `#6d7658` |
| `--sw-positive` | `#b8d16b` |
| `--sw-warning` | `#d9a441` |
| `--sw-danger` | `#f08a80` |
| `--sw-on-pine` | `#101409` |
| `--sw-plot-line` | `#b8d16b` |
| `--sw-plot-fill` | `rgb(184 209 107 / 0.16)` |
| `--sw-plot-grid` | `rgb(255 255 255 / 0.07)` |
| `--sw-scrim` | `rgb(0 0 0 / 0.62)` |
| `--sw-glass` | `rgb(24 28 16 / 0.80)` |
| `--sw-glass-strong` | `rgb(24 28 16 / 0.94)` |
| `--sw-glass-sunken` | `rgb(10 12 6 / 0.70)` |
| `--sw-glass-border` | `rgb(255 255 255 / 0.09)` |
| `--sw-wash-1` | `rgb(184 209 107 / 0.10)` |
| `--sw-wash-2` | `rgb(184 209 107 / 0.04)` |

The two-selector structure is unchanged and must stay: the
`@media (prefers-color-scheme: dark)` block scoped
`:root:not([data-theme="light"])` is the **default** (so a dark-system visitor
sees no white flash before the script runs), and `:root[data-theme="dark"]` is
the **override** the appearance control writes.

### Category bands — UNCHANGED

Nine bands need nine distinguishable hues; a three-colour brand palette cannot
supply them, and `SW-ADR-092` fixes these with a measured figure behind each.

| Category | Light | Dark |
|---|---|---|
| Groceries `--sw-cat-1` | `#4a7c59` | `#6fae82` |
| Food & Dining `--sw-cat-2` | `#b5543b` | `#e08a6f` |
| Transport `--sw-cat-3` | `#3e6b8f` | `#74a6cc` |
| Rent & Utilities `--sw-cat-4` | `#9c7a2f` | `#d4ae5e` |
| Health `--sw-cat-5` | `#2e7d8a` | `#62b8c4` |
| Entertainment `--sw-cat-6` | `#7b4b94` | `#b48ecb` |
| Shopping `--sw-cat-7` | `#a04c72` | `#d883a6` |
| Other `--sw-cat-8` | `#7d8471` | `#a8b09c` |
| Uncategorised `--sw-cat-uncat` | `#948c87` | `#9aa096` |

`Categories.jsx` reads these nine tokens off `document.documentElement` at
render time to build its swatch picker (`paletteFromStylesheet`), so they must
stay valid 6-digit hex — an `rgb()` or `oklch()` value there silently empties
the picker.

### Type

| Token | New | Old |
|---|---|---|
| `--sw-font-display` | `"Bricolage Grotesque", system-ui, -apple-system, "Segoe UI", sans-serif` | `"Instrument Serif", Georgia, serif` |
| `--sw-font-body` | `"DM Sans", system-ui, -apple-system, "Segoe UI", sans-serif` | `"Instrument Sans", system-ui, sans-serif` |
| `--sw-font-mono` | `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace` | `"IBM Plex Mono", ui-monospace, monospace` |

Scale — two steps grew, the rest are unchanged:

| Token | New | Old |
|---|---|---|
| `--sw-text-xs` | `0.75rem` | — |
| `--sw-text-sm` | `0.875rem` | — |
| `--sw-text-base` | `1rem` | — |
| `--sw-text-lg` | `1.125rem` | — |
| `--sw-text-xl` | `1.5rem` | — |
| `--sw-text-2xl` | **`2.5rem`** | `2rem` |
| `--sw-text-3xl` | **`3.75rem`** | `2.75rem` |
| `--sw-leading-tight` | **`1.08`** | `1.2` |
| `--sw-leading-normal` | `1.5` | — |

Weights unchanged: regular 400, medium 500, semibold 600. Headings never go
past 600.

**Every number keeps `.sw-num`** — `--sw-font-mono` plus
`font-variant-numeric: tabular-nums` and `font-feature-settings: "tnum" 1`, so
columns of money align. `SRC-001 §9.4` asks for this by name. Money stays
`en-IN` formatted (₹12,34,567.89) through the single formatter in
`client/src/lib/money.js`.

### Radius, shadow, motion

| Token | New | Old |
|---|---|---|
| `--sw-radius-sm` | **`5px`** | `3px` |
| `--sw-radius-md` | **`10px`** | `6px` |
| `--sw-radius-lg` | **`14px`** | `10px` |
| `--sw-radius-full` | `999px` | — |
| `--sw-shadow-sm` | `0 1px 2px rgb(20 23 14 / 0.05)` | |
| `--sw-shadow-md` | `0 3px 14px rgb(20 23 14 / 0.07)` | |
| `--sw-shadow-panel` | `0 0 0 1px rgb(20 23 14 / 0.06), 0 24px 60px rgb(20 23 14 / 0.18)` | |
| `--sw-motion-fast` | `120ms` | — |
| `--sw-motion-base` | `200ms` | — |
| `--sw-motion-ease` | **`cubic-bezier(0.2, 0.8, 0.2, 1)`** | `cubic-bezier(0.4, 0, 0.2, 1)` |

Dark-theme shadows are ambient darkness from black — `rgb(0 0 0 / 0.40)`,
`rgb(0 0 0 / 0.45)`, and a `rgb(255 255 255 / 0.08)` edge on the panel.

Spacing scale unchanged (`0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 rem`).
`--sw-target-min` stays `44px`.

## Presentation changes in `app.redesign.css`

Each one is CSS on an existing class. No markup change is required for any of
them.

**Brand mark.** `.wordmark` gains a `::before` olive tile —
`1.35ch` square, `--sw-radius-sm`, `linear-gradient(145deg, var(--sw-pine-deep),
var(--sw-pine))`, `box-shadow: 0 0 0 4px var(--sw-pine-soft)`. The gradient
direction reverses under `[data-theme="dark"]` so the lighter stop leads. This
gives both the rail and the mobile top bar a mark without a prop.

**Page titles.** `.page-title` and `.gate-title` go to `-0.03em` tracking at
weight 600. `.page-title::after` draws a `2.9rem × 3px` accent rule below the
heading, `--sw-radius-sm`, `transform-origin: left`, growing in over
`--sw-motion-base`. `.section-title` takes `--sw-font-display` at `-0.02em`.

**The hero total** (`.card-hero`, the full-width row holding the headline
figure). `position: relative; overflow: hidden`, padding
`--sw-space-6 / --sw-space-6 / --sw-space-8`, `--sw-radius-lg`,
`--sw-shadow-md`. A `::before` 4px spine down the left edge,
`linear-gradient(180deg, var(--sw-pine-deep), var(--sw-pine))`. A `::after`
`21rem` circle at `right: -5.5rem; top: -7.5rem`,
`radial-gradient(circle, var(--sw-wash-1), transparent 68%)`,
`pointer-events: none`. `.card-hero-value` at `-0.03em`; its `.card-label` at
`0.12em`.

Keep the hero as its own full-width row. It is **not** a two-column span in
`.cards` — spanning clipped `₹3,790.49` at four columns, and a lakh figure is
four characters longer.

**No labels wrap.** `white-space: nowrap` on `.btn`, `.btn-link`, `.chip`,
`.segment`, `.tab`, `.icon-btn`, `.pill`, `.bar-label`, `.cat-usage`,
`.entry-amount`. These all use `min-height` rather than `height`, so a wrapped
second line has no vertical room and sits cramped against the pill edge.

**Buttons.** `.btn` → `--sw-radius-md`, weight 600, `--sw-shadow-sm`,
`translateY(1px)` on `:active:not([aria-disabled='true'])`. `.btn-quiet` drops
the shadow and sits at weight 500. `.icon-btn` → `--sw-radius-md`, `--sw-pine`
on hover.

Keep `aria-disabled` rather than the `disabled` attribute on submit controls: a
`disabled` button leaves the tab order mid-interaction and drops focus to
`<body>`. The guard in the submit handler is what prevents the double.

**The rail.** Opaque `--sw-paper-sunken` with a `--sw-border` right edge and
`backdrop-filter: none` — the rail reads as chrome, the content column as the
subject. `.rail-item` → `--sw-radius-md` at `--sw-text-base`;
`[aria-current='page']` gets a `--sw-border` border and weight 600.

**Admin tabs become an underline, not a folder tab.** `.tabs` gets
`border-bottom: 1px solid var(--sw-border)`. `.tab` → `border-radius: 0`,
`border-width: 0 0 2px 0`, transparent, `margin-bottom: -1px`,
`--sw-text-base`. `[aria-selected='true']` → no background,
`border-bottom-color: var(--sw-pine)`, weight 600.

**Bars.** `.bar-track` height `0.55rem`. `.bar-fill` →
`linear-gradient(90deg, var(--sw-pine), var(--sw-plot-line))`,
`border-radius: --sw-radius-full`, `transform-origin: left`, growing in over
`--sw-motion-base`.

**The ribbon.** `.ribbon` height `2.1rem`, `--sw-radius-md`. `.ribbon-title`
promoted to `--sw-ink` at weight 600. **Band geometry does not change** — see
*Do not change* below.

**Entries.** `.entries` → `--sw-radius-lg`. `.entry` gets a
`--sw-pine-soft` hover (excluding `.day-head`) over `--sw-motion-fast`.
`.entry-desc` at weight 500.

**Categories.** `.cat-row` → `--sw-radius-md`, `--sw-border`, hover to
`--sw-border-strong`. `.cat-name` at `--sw-text-lg` weight 500. `.swatch`
height `2.4rem`, `--sw-radius-md`, `--sw-shadow-sm`.

**The panel.** `.scrim` gains `backdrop-filter: blur(3px)`. `.panel` →
`--sw-radius-lg` and a rise-in over `--sw-motion-base`. `.panel-title` takes
`--sw-font-display` at `-0.02em`. `input[name='amount']` grows to `3.25rem` min
height at `--sw-text-xl` — it is the field a person opens this dialog to type
in.

**The gate.** `.gate-card` → `--sw-radius-lg`, `--sw-shadow-md`, padding
`--sw-space-8 / --sw-space-6 / --sw-space-6`, rise-in. A `::before` 3px top bar,
`linear-gradient(90deg, var(--sw-pine), var(--sw-pine-deep), transparent)`.

**Inputs.** `--sw-radius-md`, `background: var(--sw-paper)`, hover to
`--sw-border-strong`.

**The segmented control.** `.segmented` padding `3px` on
`--sw-paper-sunken`; `.segment` min-height `38px` — but restored to
`--sw-target-min` under `@media (max-width: 640px)`, because the 44px floor is
a phone-width requirement (`SW-ADR-117` (5)) and the test measures the button.

**Two keyframes**, `sw-grow` (`scaleX(0)` → `scaleX(1)`) and `sw-rise`
(`opacity 0, translateY(10px)` → rest). Both are already neutralised by the
`prefers-reduced-motion: reduce` block in `tokens.css`, which sets every
duration to `0.01ms` — reduced motion means **instant**, not slower, and a test
asserts it.

## Fonts — the one item needing real work

`SW-ADR-020` rejected a CDN for the frontend on single-origin grounds and the
same reasoning applies to fonts, so the three families must be self-hosted.

**Worth knowing before you start:** there is currently **no `@font-face` rule
and no font file anywhere under `client/`**. The previous three families were
named in `tokens.css` and never loaded, so the app has been rendering system
fallbacks all along — including in every screenshot under `evidence/`.

Fetch the woff2 files (Bricolage Grotesque, DM Sans and JetBrains Mono are all
SIL Open Font License), put them in `client/public/fonts/`, and add to
`app.redesign.css`:

```css
@font-face { font-family: "Bricolage Grotesque";
             src: url("/fonts/BricolageGrotesque.woff2") format("woff2");
             font-weight: 400 700; font-display: swap; }
@font-face { font-family: "DM Sans";
             src: url("/fonts/DMSans.woff2") format("woff2");
             font-weight: 400 700; font-display: swap; }
@font-face { font-family: "JetBrains Mono";
             src: url("/fonts/JetBrainsMono.woff2") format("woff2");
             font-weight: 400 500; font-display: swap; }
```

Until then the fallback chains are `system-ui` and `ui-monospace`, so the app
degrades to the OS sans and mono rather than to Times.

## Interactions & behaviour — unchanged, and load-bearing

None of this changes. It is listed so a re-skin does not quietly break it.

**Theme.** Three exclusive states in a `role="radiogroup"` — System, Light,
Dark — in both the rail and Settings. System is the *absence* of an override,
not a third colour, which is why it is a radiogroup and not three
`aria-pressed` toggles. `client/src/lib/theme.js` writes `data-theme` on
`<html>` and persists the choice.

**The category ribbon is both the chart and the filter** (`SRC-001 §9.2`,
`SW-ADR-117`, `DESIGN-SYSTEM.md §5.1`):
- container `role="group"`, `aria-label="Spending by category"`
- each band is a native `<button>`, never a div with a click handler
- **one Tab stop for the whole ribbon** via roving tabindex; `←`/`→` move,
  `Home`/`End` jump to the ends, `Enter`/`Space` toggles, `Escape` clears
- accessible name per band: `"{Category}: ₹{amount}, {pct}% of total"`
- `aria-pressed` reflects selection
- **selection is never colour-only** — the chosen band gains an inset marker
  *and* the others dim to `0.35`. Two cues, so it survives colour blindness and
  a monochrome screen. The donut does the same: chosen slice thickens, others
  drop to `0.3`

**Two summaries, deliberately** (`SW-ADR-109`). Selecting a category re-scopes
the total, count, average, plots and list — but **not** the ribbon or the
donut, which stay whole-period so proportions remain visible and the other
categories stay reachable. `Dashboard.jsx` holds both `whole` and `scoped`.

**Band geometry stays true-proportion** (`SW-ADR-055`). `width: {percent}%` set
inline from the server's percentages, which sum to exactly 100 by
largest-remainder — do not recompute them client-side, and do not add
`min-width`, `flex-grow` or a `gap`. A 0.4% band renders 0.4% wide, stays
reachable by arrow key and still announces its full name; that is the keyboard
equivalent of a pointer target too small to hit. Separators are an
`inset -1px 0 0` box-shadow, not a border, so they never steal width from a
sliver.

**The add-expense panel is a real dialog.** Focus trapped while open and
restored to the trigger on close (on a zero timeout — the trigger sits in a
subtree that becomes `inert` in the same commit). Escape bound to the
*document*, not the panel. Background `inert`, applied to the whole `.app`
shell. Portalled to `<body>`. A dirty form confirms before discarding. **No
optimistic insert** — the row appears only after the server confirms.

**Amount field** restricts entry to two decimals via
`pattern="^[0-9]{1,15}(\.[0-9]{1,2})?$"` so the server's 422 is a backstop the
person never meets.

**Never `scrollIntoView`.** Never `overflow-x: hidden` on `body` — it hides
overflow instead of removing it, so the test passes and the content is still
unreachable.

## Screens

Seven, all in the prototype, all layout-unchanged.

**Sign in / Gate** (`Gate.jsx`) — one component for sign-in and sign-up,
because they are the same form plus one field and switching must not lose what
was typed. Centred card, max ~26rem. A `reason` banner when a session ended
mid-use. Field-level errors under the field, never in a toast.

**Dashboard** (`Dashboard.jsx`) — in order: page head with *Add expense*;
period chips (This month / Last month / Last 30 days); the full-width hero
total with a delta line; three stat cards (Entries / Daily average / On track
for) on `repeat(auto-fit, minmax(13rem, 1fr))`; two chart cards on
`repeat(auto-fit, minmax(20rem, 1fr))` (Spending over time, By category donut +
legend); the ribbon with its legend; two more chart cards (Running total, By
day of the week); the Entries heading; the day-grouped entry list with a
per-day subtotal beside each date.

Daily average shows `Not yet`, never `₹0.00`, when no day has elapsed —
`₹0.00` reads as "spent nothing" on the first screen a new account sees
(`SW-ADR-053`). On track for shows `—` when the period has ended.

**Categories** (`Categories.jsx`) — an *Add a category* card (name field,
nine-swatch picker read from the live stylesheet, Add) then one row per
category with a colour dot, name, this-month usage, Edit and Delete. Deleting
NULLs the expenses and never deletes them; the confirm names the real count.

**Settings** (`Settings.jsx`) — five stacked cards: Your name, Appearance,
Password, Your data (JSON export), and Closing your account. The last is
`--sw-danger`-bordered and holds two side-by-side, equally weighted options —
*Pause it* and *Close it* — each with its own two-step confirm. Deliberately
not a primary action with the other tucked underneath: both mean "I am done" in
ordinary English, so the layout has to make a person read which is which
rather than reach for whichever is larger. The buttons are shrink-to-fit for
the same reason.

**Admin** (`Admin.jsx`) — four tabs: Overview (four stat cards + two chart
cards), Accounts (search, a three-state deleted filter, a table with per-row
View / Sign out / Deactivate / Promote / Reset password), Signed in now, Audit
log. The Accounts table sits in its own `overflow-x: auto` container so a wide
table never scrolls the page sideways at phone width.

The admin user-detail pane shows one person's total, count, daily average and
day-by-day line — and never a category, a description or a single row. Do not
add a `Donut`, a `Ribbon` or an `EntryList` there; the response has no field to
feed them, and that boundary is the entire content of `CR-001`.

**Add-expense panel** (`ExpensePanel.jsx`) — Amount, Date, Category, Note.

## Phone width

`SRC-001 §12.1` excludes a native app, so the phone-width web experience is the
entire mobile product. Single column below 640px; the add-expense panel enters
from the **bottom**, not the right; the ribbon stays horizontal and scrolls;
the entry list drops to two lines per row. **Nothing is hidden at phone width
that exists on desktop.** Every control keeps its 44×44 CSS px floor.

The prototype in this bundle is desktop-only — take the phone rules from
`app.css`'s existing media queries, not from it.

## Accessibility floor

`WCAG 2.1 AA` (`SW-ADR-117`), and the build enforces it:

| | Rule |
|---|---|
| Focus | 2px solid outline, ≥3:1 against its background, 2px offset, **one** global `:focus-visible` rule in `tokens.css`. `outline: none` never ships without a replacement |
| Motion | `prefers-reduced-motion: reduce` → instant |
| Text contrast | ≥4.5:1 |
| Component contrast | ≥3:1 |
| Targets | ≥44×44 CSS px at phone width |
| Colour | never the only carrier of meaning |

`--sw-ink-faint` must never carry content — placeholder and disabled text only,
where WCAG exempts the requirement.

## Verification — required before merge

```
py tools/contrast.py
npm run lint:tokens
pytest tests/browser
```

**`tools/contrast.py` is the one that matters here.** Every figure in
`DESIGN-SYSTEM.md §2.1` and `CONTRAST.md` was computed from the *old* hexes and
none of them describe these. The tool measures every pair in both themes,
composites translucent surfaces before measuring, and fails the build on a pair
below its floor. The new values were chosen to clear the floors but they were
estimated, not measured — run it.

Pairs to watch:

- `--sw-border-strong` `#7f8a63` vs `--sw-paper` — needs ≥3:1 (a UI component).
  Aimed at ~3.3:1, so it has the least headroom of anything here.
- `--sw-ink-muted` `#4f5643` on paper, raised and sunken — needs ≥4.5:1.
- `--sw-pine` `#4e5f22` on paper and raised — needs ≥4.5:1; and
  `--sw-on-pine` `#f7faee` **on** it, likewise.
- The glass alphas are unchanged at 0.80 / 0.93 / 0.70, but the surface hexes
  behind them moved, so every **composited** figure moved too.

If a pair fails, adjust tone within the hue rather than reaching for a new
colour — that is the instruction `SW-ADR-092` already gives for the category
bands, and `SW-ADR-131` is the precedent for following it.

`lint:tokens` will also catch, and should keep catching: a raw hex outside
`tokens.css`, a second money formatter, `paise / 100` anywhere but
`lib/money.js`, more than one `:focus-visible` rule, and any `outline: none`.

## Documentation to update

The design system is a binding standard here, not a description, so a palette
change is a documentation change too:

- `docs/05 B DesignSystem/DESIGN-SYSTEM.md` — §1 (the client brief quote still
  says "paper and pine green" and names the old three fonts), §2 (the token
  table), §2.1 (the measured figures — paste what the tool prints, do not
  assert them), §3 (the type table).
- `docs/05 B DesignSystem/CONTRAST.md` — regenerated by the tool.
- A **superseding ADR** recording the palette and type change, so
  `SW-ADR-147`'s dark-mode reasoning and `SW-ADR-092`'s band floors have
  something current to point at. Add it to
  `docs/01 ADR/ADR_DECISION_RELEASE_LEDGER.tsv`.

## What NOT to change

- Any `.jsx` file. If you find yourself editing one, the change belongs in CSS.
- Token *names*. `--sw-pine` means "the accent" and is referenced across
  `app.css`, the docs and several ADRs.
- The nine category band colours.
- `--sw-warning` and `--sw-danger`. A warning that reads as the accent is not a
  warning.
- The ribbon's proportional geometry, its roving tabindex, or its two selection
  cues.
- The two-summary rule: the ribbon and donut stay whole-period.
- The dialog's focus trap, `inert` handling, document-level Escape, or the
  absence of an optimistic insert.
- The single `:focus-visible` rule's location in `tokens.css`.
- The absence of a router.

## Files in this bundle

| File | What it is |
|---|---|
| `README.md` | this document |
| `docs-design-system-tokens.css` | **drop-in.** Replaces `docs/05 B DesignSystem/tokens.css` |
| `app.redesign.css` | **drop-in.** New `client/src/styles/app.redesign.css` |
| `SpendWise.dc.html` | **reference only.** Standalone HTML prototype of all seven screens, both themes, with working nav, filters, theme toggle and panel. Do not copy into `client/` |

`SpendWise.dc.html` needs `support.js` beside it to run, which is not part of
this bundle — read it as a spec, or view it in the design tool it came from.
