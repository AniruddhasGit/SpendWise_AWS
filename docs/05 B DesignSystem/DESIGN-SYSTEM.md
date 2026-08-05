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

---

## §1 — What the client asked for

> "Look and feel: paper and pine green, not the default blue SaaS dashboard. Instrument Serif
> for display, Instrument Sans for body, IBM Plex Mono for every number. Tabular figures so
> columns of money line up. Works down to phone width, keyboard focus visible, reduced motion
> respected." — `SRC-001 §9.4`

That is the whole brief. Everything below is that sentence made testable.

---

## §2 — Colour

**No component ever references a raw hex.** Components reference semantic tokens; tokens hold
the hex. This is enforceable by grep and is checked in this goal's Definition of Done.

| Token | Value | Use |
|---|---|---|
| `--sw-paper` | `#faf7f2` | the page. Warm off-white, never pure white. |
| `--sw-paper-raised` | `#ffffff` | cards and the add-expense panel, lifted off the page. |
| `--sw-paper-sunken` | `#f0ece4` | table header rows, inset wells. |
| `--sw-ink` | `#1c1917` | primary text. Warm near-black, never #000. |
| `--sw-ink-muted` | `#57534e` | secondary text, labels, timestamps. |
| `--sw-ink-faint` | `#78716c` | placeholder and disabled text ONLY. Fails AA on body copy — never use it for content. |
| `--sw-pine` | `#2d5a3d` | the accent. Primary buttons, active states, links. |
| `--sw-pine-deep` | `#1b3826` | pressed and hover on pine. |
| `--sw-pine-soft` | `#e6ede8` | tinted backgrounds behind pine content. |
| `--sw-border` | `#ddd6cb` | hairlines, input borders, band separators. |
| `--sw-border-strong` | `#a8a29e` | focus-adjacent borders, table rules. |
| `--sw-positive` | `#2d5a3d` | same as pine — under-budget, success. |
| `--sw-warning` | `#8a5a1f` | approaching a limit. |
| `--sw-danger` | `#9c2f28` | destructive actions, validation errors. |

**Fonts are self-hosted**, not fetched from Google Fonts. `SW-ADR-020` rejected a CDN for the
frontend on single-origin grounds; the same reasoning applies to the fonts.

### §2.1 — Measured text contrast

| Foreground | Background | Measured | Needs | |
|---|---|---|---|---|
| `ink` #1c1917 | `paper` #faf7f2 | **16.37:1** | 4.5 | PASS |
| `ink` #1c1917 | `paper-raised` #ffffff | **17.49:1** | 4.5 | PASS |
| `ink` #1c1917 | `paper-sunken` #f0ece4 | **14.84:1** | 4.5 | PASS |
| `ink-muted` #57534e | `paper` #faf7f2 | **7.14:1** | 4.5 | PASS |
| `ink-muted` #57534e | `paper-raised` #ffffff | **7.63:1** | 4.5 | PASS |
| `pine` #2d5a3d | `paper` #faf7f2 | **7.44:1** | 4.5 | PASS |
| `pine` #2d5a3d | `paper-raised` #ffffff | **7.95:1** | 4.5 | PASS |
| `danger` #9c2f28 | `paper` #faf7f2 | **6.89:1** | 4.5 | PASS |
| `warning` #8a5a1f | `paper` #faf7f2 | **5.52:1** | 4.5 | PASS |
| `paper` #faf7f2 | `pine` #2d5a3d | **7.44:1** | 4.5 | PASS |
| `paper` #faf7f2 | `danger` #9c2f28 | **6.89:1** | 4.5 | PASS |

**All pairs pass.**

`--sw-ink-faint` is deliberately absent from that table. It is for placeholder and disabled
text only, where WCAG exempts the requirement. **It must never carry content.**

### §2.2 — The eight seeded categories

Ruled by `SW-ADR-092`. Measured against `--sw-paper` `#faf7f2`; the floor is 3:1 because a
band is a UI component, not text.

| Category | Token value | Measured vs paper | |
|---|---|---|---|
| Groceries | `#4a7c59` | **4.55:1** | PASS |
| Food & Dining | `#b5543b` | **4.57:1** | PASS |
| Transport | `#3e6b8f` | **5.30:1** | PASS |
| Rent & Utilities | `#9c7a2f` | **3.75:1** | PASS |
| Health | `#2e7d8a` | **4.45:1** | PASS |
| Entertainment | `#7b4b94` | **6.00:1** | PASS |
| Shopping | `#a04c72` | **5.21:1** | PASS |
| Other | `#7d8471` | **3.63:1** | PASS |
| Uncategorised | `#948c87` | **3.09:1** | PASS |

**All bands pass.**

"Uncategorised" is `#948c87` — a warm stone grey, deliberately distinct from the seeded
"Other" `#7d8471`, and it always sorts last regardless of size (`SW-ADR-113`).

> **Adjusted here, and why that is the process working.** `SW-ADR-113` specified `#a8a29e`.
> Measured against paper it is **2.36:1** — below the 3:1 floor a UI component needs. It was
> darkened within the same hue to the value above. `SW-ADR-092` anticipated this exact case:
> *"the design system adopts these as tokens and MUST verify each at >=3:1 against the paper
> surface, adjusting tone within hue if any fails."* The instruction was followed rather than
> the number being taken on trust — one of nine bands failed, and a document that asserted
> compliance instead of computing it would have shipped it.

---

## §3 — Type

| Role | Family | Size | Weight |
|---|---|---|---|
| Display — the headline total | Instrument Serif | `--sw-text-3xl` | regular |
| Section heading | Instrument Sans | `--sw-text-xl` | semibold |
| Body | Instrument Sans | `--sw-text-base` | regular |
| Label, timestamp | Instrument Sans | `--sw-text-sm` | medium |
| **Every number** | **IBM Plex Mono** | inherits | regular |

**Every number uses `.sw-num`**, which sets `font-variant-numeric: tabular-nums`. This is not
decoration — `SRC-001 §9.4` asks for it by name so columns of money align, and a proportional
digit set makes a column of rupee amounts unreadable.

Money is formatted `en-IN` — ₹12,34,567.89, not ₹1,234,567.89 (`SW-ADR-056`). One shared
formatter; no component invents its own.

---

## §4 — Space, radius, shadow, motion

One scale each, in `tokens.css`. Motion is `--sw-motion-fast` for state changes and
`--sw-motion-base` for the panel.

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

## §7 — Phone width

`SRC-001 §12.1` excludes a native app, so **the phone-width web experience is the entire
mobile product.** Layout is single-column below 640px; the add-expense panel enters from the
bottom rather than the right; the ribbon stays horizontal and scrolls if bands get narrow;
the entry list drops to two lines per row. Nothing is hidden at phone width that exists on
desktop.

---

## §8 — What this document does not decide

It binds presentation. It is **not** a schema source, and it does not decide behaviour — which
numbers move when a band is selected is `SW-ADR-113`, not this page.
