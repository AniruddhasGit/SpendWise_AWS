# SpendWise — Design System

| Field | Value |
|---|---|
| Version | v0.1-draft · **binding UX standard** |
| Decision status | NOT_DECIDED (fail-closed) |
| Sources | `SRC-001 §9.2`, `§9.4` · `SW-ADR-092` (categories) · `SW-ADR-117` (accessibility) · `SW-ADR-109` (ribbon) · `SW-ADR-056` (money format) |
| Conformance target | **WCAG 2.1 AA** (`SW-ADR-117`) |

> **This binds front-end engineering only. It is NOT a schema source.**
> Every contrast figure below was **computed** from the hex values in `tokens.css`, not
> asserted. The script is in the goal's evidence; re-run it rather than trusting this page.
>
> **As of `SW-ADR-147` that is a program, not a practice.** `tools/contrast.py` measures every
> pair in **both themes**, composites translucent surfaces before measuring, and **fails the
> build on a pair below its floor** — not only on drift. The live table is
> [`CONTRAST.md`](CONTRAST.md); the tables in §2.1 and §2.2 below are the light theme's, kept
> here for reading.
>
> It found one on its first honest run. `--sw-border-strong` was `#a8a29e` — **2.36:1** against
> paper, below the 3:1 §6 requires of a UI component, and the same hex `SW-ADR-131` had already
> measured, found failing, and darkened *for the Uncategorised band*. A hand-maintained check
> measures what someone remembered to list; nothing listed the borders. Now `#8a837b`, 3.50:1.

---

## §1 — What the client asked for

> "Look and feel: paper and pine green, not the default blue SaaS dashboard. Instrument Serif
> for display, Instrument Sans for body, IBM Plex Mono for every number. Tabular figures so
> columns of money line up. Works down to phone width, keyboard focus visible, reduced motion
> respected." — `SRC-001 §9.4`

That is the whole brief. Everything below is that sentence made testable.

> **`CR-002`, 2026-08-21 — the visual half of that sentence has been reversed by the client.**
> The palette is no longer paper-and-pine and the three named families are no longer the ones in
> use. The quote above is **left standing verbatim** because `SRC-001` is fingerprinted and
> because the record of what was originally asked for is worth more than a tidy document.
> What it asked for now: greenish-white `#f2f5e9`, olive `#4e5f22`, near-black `#14170e`;
> Bricolage Grotesque, DM Sans, JetBrains Mono. See `docs/15 ChangeRequest/CR-002_visual-identity.md`
> and `SW-ADR-152`.
>
> **Its accessibility clauses were not reversed and are still binding** — tabular figures, phone
> width, visible keyboard focus, reduced motion respected. Those are `SW-ADR-117`, and a palette
> change does not reach them.

---

## §2 — Colour

**No component ever references a raw hex.** Components reference semantic tokens; tokens hold
the hex. This is enforceable by grep and is checked in this goal's Definition of Done.

| Token | Value | Use |
|---|---|---|
| `--sw-paper` | `#f2f5e9` | the page. Greenish white, never pure white. |
| `--sw-paper-raised` | `#fbfcf6` | cards and the add-expense panel, lifted off the page. |
| `--sw-paper-sunken` | `#eaefdc` | table header rows, inset wells. |
| `--sw-ink` | `#14170e` | primary text. Near-black with an olive cast, never #000. |
| `--sw-ink-muted` | `#4f5643` | secondary text, labels, timestamps. |
| `--sw-ink-faint` | `#7c8468` | placeholder and disabled text ONLY. Fails AA on body copy — never use it for content. |
| `--sw-pine` | `#4e5f22` | **the accent — olive.** Primary buttons, active states, links. |
| `--sw-pine-deep` | `#354115` | pressed and hover on the accent. |
| `--sw-pine-soft` | `#e2eaca` | tinted backgrounds behind accent content. |
| `--sw-border` | `#d8e0c2` | hairlines, input borders, band separators. |
| `--sw-border-strong` | `#7f8a63` | focus-adjacent borders, table rules. |
| `--sw-positive` | `#4e5f22` | same as the accent — under-budget, success. |
| `--sw-warning` | `#8a5a1f` | approaching a limit. **Unchanged by `CR-002`.** |
| `--sw-danger` | `#9c2f28` | destructive actions, validation errors. **Unchanged by `CR-002`.** |

**Fonts are self-hosted**, not fetched from Google Fonts. `SW-ADR-020` rejected a CDN for the
frontend on single-origin grounds; the same reasoning applies to the fonts.

> Until 2026-08-21 that sentence was **aspirational, not true**. There was no `@font-face` rule and
> no font file anywhere under `client/`: the families were named in `tokens.css` and never loaded,
> so the app rendered system fallbacks — including in every screenshot under `evidence/` from
> before that date. Six woff2 files now ship under `client/public/fonts/` (`SW-ADR-152`).

### §2.1 — Measured text contrast

**Computed, not asserted.** Every figure below is pasted from `py tools/contrast.py`, which
measures all 26 pairs in each theme, composites translucent surfaces before measuring, and exits
non-zero on any pair below its floor. `CONTRAST.md` is its generated output. Re-run it after
touching any colour — including a colour that is not in this table, because a pair has two sides.

Text, floor 4.5:1 (SC 1.4.3):

| Foreground | Background | Measured | Needs | |
|---|---|---|---|---|
| `ink` #14170e | `paper` #f2f5e9 | **16.41:1** | 4.5 | PASS |
| `ink` #14170e | `paper-raised` #fbfcf6 | **17.57:1** | 4.5 | PASS |
| `ink` #14170e | `paper-sunken` #eaefdc | **15.43:1** | 4.5 | PASS |
| `ink` #14170e | `glass` rgb(251 252 246 / 0.80) | **17.33:1** | 4.5 | PASS |
| `ink-muted` #4f5643 | `paper` #f2f5e9 | **6.93:1** | 4.5 | PASS |
| `ink-muted` #4f5643 | `paper-raised` #fbfcf6 | **7.42:1** | 4.5 | PASS |
| `ink-muted` #4f5643 | `glass` rgb(251 252 246 / 0.80) | **7.32:1** | 4.5 | PASS |
| `pine` #4e5f22 | `paper` #f2f5e9 | **6.37:1** | 4.5 | PASS |
| `pine` #4e5f22 | `paper-raised` #fbfcf6 | **6.82:1** | 4.5 | PASS |
| `pine` #4e5f22 | `glass` rgb(251 252 246 / 0.80) | **6.73:1** | 4.5 | PASS |
| `danger` #9c2f28 | `paper` #f2f5e9 | **6.67:1** | 4.5 | PASS |
| `warning` #8a5a1f | `paper` #f2f5e9 | **5.34:1** | 4.5 | PASS |
| `on-pine` #f7faee | `pine` #4e5f22 | **6.66:1** | 4.5 | PASS |
| `on-pine` #f7faee | `danger` #9c2f28 | **6.97:1** | 4.5 | PASS |

UI components, floor 3:1 (SC 1.4.11):

| Foreground | Background | Measured | Needs | |
|---|---|---|---|---|
| `focus-color` var(--sw-pine) | `paper` #f2f5e9 | **6.37:1** | 3.0 | PASS |
| `focus-color` var(--sw-pine) | `glass` rgb(251 252 246 / 0.80) | **6.73:1** | 3.0 | PASS |
| `border-strong` #7f8a63 | `paper` #f2f5e9 | **3.33:1** | 3.0 | PASS |

**All pairs pass, in both themes — light 26/26, dark 26/26.**

`--sw-ink-faint` is deliberately absent from that table. It is for placeholder and disabled
text only, where WCAG exempts the requirement. **It must never carry content.**

### §2.2 — The eight seeded categories

Ruled by `SW-ADR-092`. Measured against `--sw-paper` `#f2f5e9`; the floor is 3:1 because a
band is a UI component, not text.

| Category | Token value | Measured vs paper | |
|---|---|---|---|
| Groceries | `#4a7c59` | **4.40:1** | PASS |
| Food & Dining | `#b5543b` | **4.43:1** | PASS |
| Transport | `#3e6b8f` | **5.13:1** | PASS |
| Rent & Utilities | `#9c7a2f` | **3.63:1** | PASS |
| Health | `#2e7d8a` | **4.30:1** | PASS |
| Entertainment | `#7b4b94` | **5.80:1** | PASS |
| Shopping | `#a04c72` | **5.04:1** | PASS |
| Other | `#7d8471` | **3.51:1** | PASS |
| Uncategorised | `#928a85` | **3.07:1** | PASS |

**All bands pass.**

"Uncategorised" is `#928a85` — a warm stone grey, deliberately distinct from the seeded
"Other" `#7d8471`, and it always sorts last regardless of size (`SW-ADR-131`).

> **Adjusted twice, and the second time is the more interesting one.**
>
> **2026-08-06 (`SW-ADR-131`, `SW-ADR-147`).** The superseded `SW-ADR-113` specified `#a8a29e`,
> which measured **2.36:1** against the then-current paper — below the 3:1 floor a UI component
> needs. Darkened within the same hue to `#948c87`.
>
> **2026-08-21 (`CR-002`, `SW-ADR-152`).** `#948c87` then failed at **2.99:1** — by 0.01 — without
> anyone touching it. **The band did not change; the ground under it did.** The palette moved from
> `#faf7f2` to `#f2f5e9`, and a change request that explicitly listed the nine bands as *unchanged*
> silently re-opened all nine. Darkened within the hue again to `#928a85`, **3.07:1**, hue drift
> `0.00°`. `#938b86` also cleared the floor at 3.029:1 and was rejected — 0.029 of headroom is how
> the first adjustment came to be needed.
>
> `SW-ADR-092` anticipated the mechanism: *"the design system adopts these as tokens and MUST
> verify each at >=3:1 against the paper surface, adjusting tone within hue if any fails."* Three
> times now that instruction has been the thing standing between this project and a shipped
> accessibility failure, and all three were caught by measuring rather than by reasoning.
>
> **`--sw-cat-uncat` currently has the least headroom of any pair in the system, at +0.07. Any
> future change to `--sw-paper` breaks it first.**

---

## §3 — Type

Changed by `CR-002` / `SW-ADR-152`. Display is now a grotesque rather than a serif, so the
headline total and the page titles read as interface rather than as editorial.

| Role | Family | Size | Weight |
|---|---|---|---|
| Display — the headline total | Bricolage Grotesque | `--sw-text-3xl` (3.75rem) | semibold |
| Page / section heading | Bricolage Grotesque | `--sw-text-xl` | semibold |
| Body | DM Sans | `--sw-text-base` | regular |
| Label, timestamp | DM Sans | `--sw-text-sm` | medium |
| **Every number** | **JetBrains Mono** | inherits | regular |

Headings never go past weight 600. `--sw-text-2xl` is 2.5rem and `--sw-leading-tight` is 1.08.

**All three are self-hosted**, six woff2 files under `client/public/fonts/`, declared in
`app.redesign.css` — `SW-ADR-020` rejects a CDN. **Two subsets per family, not one:** `U+20B9`,
the rupee sign, is in `latin-ext`, not `latin` (which carries `U+20AC`, the euro). A latin-only
build renders every ₹ from a fallback font beside digits from JetBrains Mono. Verified in a
browser, not assumed: with the faces loaded, `document.fonts.check('500 16px "JetBrains Mono"',
'₹')` is `true` and ₹ measures 20.00px against 21.99px for the fallback.

**Every number uses `.sw-num`**, which sets `font-variant-numeric: tabular-nums`. This is not
decoration — `SRC-001 §9.4` asks for it by name so columns of money align, and a proportional
digit set makes a column of rupee amounts unreadable.

Money is formatted `en-IN` — ₹12,34,567.89, not ₹1,234,567.89 (`SW-ADR-056`). One shared
formatter; no component invents its own.

---

## §4 — Space, radius, shadow, motion

One scale each, in `tokens.css`. Motion is `--sw-motion-fast` (120ms) for state changes and
`--sw-motion-base` (200ms) for the panel.

Changed by `CR-002` / `SW-ADR-152`: radii `3 / 6 / 10px` → **`5 / 10 / 14px`** — the old 6px read
as a form control on a card the size of the hero, where 10/14 reads as a surface. Easing
`cubic-bezier(0.4, 0, 0.2, 1)` → **`cubic-bezier(0.2, 0.8, 0.2, 1)`**. Shadows re-tinted to the new
ink. The spacing scale and `--sw-target-min` (44px) are unchanged.

**Under `prefers-reduced-motion: reduce`, every transition and animation is disabled** — the
add-expense panel *appears instantly* rather than sliding. "Appears instantly" is the
definition, and it is what a test asserts (`SW-ADR-117`).

---

## §5 — Components, with all five states

Every component specifies default · hover · focus · disabled · error/empty.

### Button
| State | Treatment |
|---|---|
| default | `--sw-pine` fill, `--sw-paper` text, `--sw-radius-md` |
| hover | `--sw-pine-deep` fill |
| focus | the global focus ring — never removed |
| disabled | `--sw-paper-sunken` fill, `--sw-ink-faint` text, `cursor: not-allowed`, `aria-disabled` |
| destructive | `--sw-danger` fill; always behind a confirm (`SW-ADR-119`) |

Minimum target **44×44 CSS px** at phone width.

### Input
default `--sw-border` hairline · focus the ring plus `--sw-pine` border · error `--sw-danger`
border with the message below the field, not in a toast · disabled `--sw-paper-sunken`.

The amount field restricts entry to two decimal places (`SW-ADR-112`) so the server's 422 is a
backstop the user should never meet.

### Card · Table row · Chip · Panel
Card `--sw-paper-raised` on `--sw-shadow-sm`. Table rows separate with `--sw-border`, never
with fill striping. Chips (the period picker) are `--sw-radius-full`, `aria-pressed` on the
active one. The panel is a real dialog — focus trapped on open, focus restored on close,
Escape closes, the background is `inert`, and a dirty form confirms before discarding.

### §5.1 — The category ribbon — the one that needed a ruling

`SRC-001 §9.2` makes this **both the chart and the filter**. `SW-ADR-117` makes it a control
rather than a picture:

- Container `role="group"`, `aria-label="Spending by category"`.
- **Each band is a native `<button>`.**
- **One Tab stop for the whole ribbon** (roving tabindex). `←`/`→` move between bands,
  `Home`/`End` jump to first/last, `Enter`/`Space` toggles the filter, `Escape` clears it.
- Accessible name per band: `"{Category}: ₹{amount}, {pct}% of total"`.
- `aria-pressed` reflects selection.
- **Selection is never colour-only** — the active band gains an outline marker *and* the others
  dim. Two cues, so it survives colour blindness and a monochrome screen.
- 1px `--sw-border` separators divide adjacent bands.
- Geometry stays true-proportion (`SW-ADR-055`): a sliver band is still reachable by arrow key
  and still announces its full name. **That is the keyboard equivalent of a pointer target too
  small to hit.**

Selecting a band re-scopes the total, count, average, day bars and list — but **not the ribbon
itself**, which stays whole-period so proportions remain visible and other bands stay
reachable (`SW-ADR-109`).

### §5.2 — The per-day bar chart
`aria-hidden="true"` decoration inside a labelled container. Its accessible data representation
is the date-grouped entry list already on the page — the same numbers, already reachable.

---

## §6 — Accessibility floor

| | Rule |
|---|---|
| Target | **WCAG 2.1 AA** |
| Focus | 2px solid outline, ≥3:1 against the adjacent background, 2px offset, one global `:focus-visible` rule. **`outline: none` never ships without a replacement.** |
| Motion | `prefers-reduced-motion: reduce` → everything instant |
| Text contrast | ≥4.5:1 — measured in §2.1 |
| Component contrast | ≥3:1 — measured in §2.2 |
| Targets | ≥44×44 CSS px at phone width |
| Ribbon | a real control — §5.1 |
| Colour | never the only carrier of meaning |

---

## §6.1 — Dark mode and glass — `SW-ADR-147`

Two themes. `@media (prefers-color-scheme: dark)` is the **default**, so a person whose system is
dark never sees a white flash before the script runs; `:root[data-theme="dark"]` is the
**override** the appearance control writes, and the media query is scoped
`:root:not([data-theme="light"])` so an explicit light choice beats a dark system.

**Dark is not an inversion.** The light accent `#4e5f22` measures **2.74:1** on the dark
surface `#0d0f09` — far under the 3:1 a component needs — so dark uses a lighter tint of the
same hue, `#b8d16b`, at **11.36:1**; five of the nine category bands are re-tinted the
same way. Every replacement was chosen by running the tool until it passed. (Updated by
`SW-ADR-152`: the figures above were `#2d5a3d` / 1.6:1 / `#7fc79a` before `CR-002` moved the
palette. The *reasoning* is `SW-ADR-147`'s and did not change; only the hexes it applies to did.)

**Glass composites, so its alpha is a measured floor.** `--sw-glass` is
`rgb(251 252 246 / 0.80)` because that is where `--sw-ink-muted` on glass still clears 4.5:1 over
the accent wash — it currently measures **7.32:1**. Lowering it for a prettier blur is a change the gate refuses — the colour a person
reads through glass is `surface × α + backdrop × (1−α)`, which is written down nowhere and has to
be calculated.

| Token | Use |
|---|---|
| `--sw-glass` | cards, the sidebar, panels |
| `--sw-glass-strong` | anything overlapping content — the dialog |
| `--sw-glass-sunken` | wells and table headers |
| `--sw-glass-border` | the 1px highlight that makes an edge read as glass |
| `--sw-glass-blur` | `backdrop-filter` radius |
| `--sw-wash-1`, `--sw-wash-2` | the two olive radials the glass sits on |
| `--sw-on-pine` | text on an accent or danger fill |
| `--sw-plot-line`, `--sw-plot-fill`, `--sw-plot-grid` | the line chart. Not category colours |

`backdrop-filter` is **progressive enhancement**: where it is unsupported the surface is still
opaque enough to clear every floor on its own, because the figures are computed from the alpha,
never from the blur.

---

## §7 — Phone width

`SRC-001 §12.1` excludes a native app, so **the phone-width web experience is the entire
mobile product.** Layout is single-column below 640px; the add-expense panel enters from the
bottom rather than the right; the ribbon stays horizontal and scrolls if bands get narrow;
the entry list drops to two lines per row. Nothing is hidden at phone width that exists on
desktop.

---

## §8 — What this document does not decide

It binds presentation. It is **not** a schema source, and it does not decide behaviour — which
numbers move when a band is selected is `SW-ADR-109`, not this page.
(This pointer read `SW-ADR-131` until 2026-08-05 — the Uncategorised bucket, not the
re-scoping rule. §5.1 above had it right all along.)
