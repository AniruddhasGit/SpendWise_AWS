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

> **Revision 2026-10-18 (b) — new money.** Fifth visual revision, the same day as the fourth. The
> owner saw the violet "liquid glass" draft and said: *"this looks ugly, it's a spending app about
> money, make a design about that."* The palette is now **emerald + champagne gold, dark first**
> (deep forest ground `#06140f`; warm ivory paper `#f7f4ec` in light). Texture is generated banknote
> **guilloché**; the hero object is a **glass bank card** over a molten emerald→gold liquid orb. The
> photo backdrops are retired. Violet, purple and pink are gone from every token. Geometry, type
> (Geist) and motion carry over from the fourth revision. Token NAMES are unchanged; `--sw-pine` is
> now emerald. `py tools/contrast.py` is green in both themes (26/26, 26/26). Worst-case contrast
> over the guilloché and the orb is §2.4.

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

| Token | Value (light / dark) | Use |
|---|---|---|
| `--sw-paper` | `#f7f4ec` / `#06140f` | the page's opaque ground; `body` background-color. Uncategorised measures 3.08:1 on it (§2.2). |
| `--sw-paper-raised` | `#fffdf8` / `#0f2119` | CONTENT-tier surface: `.card .entries .table-wrap .state`. Opaque, always. |
| `--sw-paper-sunken` | `#efeadd` / `#04100b` | wells, coin chips. **Never** a bare category band on it in light (Uncategorised 2.82:1); use the `.sw-coin`/`.sw-swatch` rim. |
| `--sw-ink` | `#0f1f18` / `#f3f0e6` | primary text: emerald-black / ivory. |
| `--sw-ink-muted` | `#4a5a51` / `#a6b9ae` | secondary text, labels, timestamps. |
| `--sw-ink-faint` | `#8e9a92` / `#6b8277` | placeholder and disabled text ONLY. Never content. |
| `--sw-pine` | `#0b6b4a` / `#3fd9a2` | **the accent: emerald.** Primary buttons, links, focus, selection. The name is historical. |
| `--sw-pine-deep` | `#08543a` / `#72e8bd` | hover on the accent. |
| `--sw-pine-soft` | `#dcefe5` / `#0e3527` | tinted ground behind accent content, input focus halo, `.pill`. |
| `--sw-gold` | `#7a5810` / `#e8c77a` | **gold TEXT**: totals, eyebrows, highlights. |
| `--sw-gold-fill` · `-deep` · `-soft` · `--sw-on-gold` | `#e2c276` · `#c9a24e` · `#f4e9cc` · `#1a1305` (light) | gold SURFACES: chip, foil, `.btn-gold`, `.pill-gold`. |
| `--sw-border` | `#e2dccb` / `#183429` | hairlines, input borders, ledger rules. |
| `--sw-border-strong` | `#7a7663` / `#6a9783` | the 3:1 UI-component border; the coin rim. |
| `--sw-positive` | `#0b6b4a` / `#4be0a6` | income, under budget, success. Always with a "+" or a word. |
| `--sw-warning` | `#8a520c` / `#f2b657` | approaching a limit. |
| `--sw-danger` · `-soft` | `#b3261e` / `#ff8b7b` | **overspend and destructive ONLY.** Coral, never for ordinary spending. |
| `--sw-on-pine` | `#ffffff` / `#04140d` | text on an emerald or danger fill. |
| `--sw-orb-deep` · `-emerald` · `-gold` | `#1e8c63 #3ccb97 #d9b460` / `#0e5a3f #2bd49a #e8c77a` | **decoration only**: the liquid orb. |
| `--sw-sheen-a/b` · `--sw-sheen-alpha` | emerald + gold at 0.18 | the metallic sheen on primary pills. Cap 0.18. |
| `--sw-guilloche` · `-opacity` · `-card-opacity` | `#8a6a1f` .08/.14 / `#e8c77a` .07/.10 | the banknote line pattern, a mask fill. |
| `--sw-card-*` | one face in both themes | the bank card: `face-1/2` `#0a271d → #0e3226`, `ink` `#f3f0e6`, `muted` `#bccdc2`, `gold` `#e8c77a`, `positive` `#5fe6b0`, `negative` `#ffb0a2`; `--sw-card-glass*` for the translucent hero card. |
| `--sw-bg-1/2/3` | ivory → parchment (light) · forest → deep green (dark) | the page gradient, `background-image` only. |

**Fonts are self-hosted**, not fetched from Google Fonts. `SW-ADR-020` rejected a CDN for the
frontend on single-origin grounds; the same reasoning applies to the fonts.

> Until 2026-08-21 that sentence was **aspirational, not true**. There was no `@font-face` rule and
> no font file anywhere under `client/`: the families were named in `tokens.css` and never loaded,
> so the app rendered system fallbacks — including in every screenshot under `evidence/` from
> before that date. Six woff2 files shipped under `client/public/fonts/` (`SW-ADR-152`). Since
> 2026-10-18 the system uses one file, `Geist-Variable.woff2` (§3).

### §2.1 — Measured text contrast

**Computed, not asserted.** The rows below are copied from `CONTRAST.md`, which `py tools/contrast.py`
generates. The tool measures all 26 pairs in each theme, composites translucent glass over `--sw-paper`,
and exits non-zero on any pair below its floor. The dark theme's rows are in `CONTRAST.md`. Re-run the
tool after touching any colour.

Light theme (key rows; the full 26 per theme are in `CONTRAST.md`):

| Foreground | Background | Measured | Floor | | Use |
|---|---|---:|---:|---|---|
| `--sw-ink` | `--sw-paper` | **15.54:1** | 4.5 | PASS | body text on the page |
| `--sw-ink` | `--sw-paper-raised` | **16.80:1** | 4.5 | PASS | body text on a card |
| `--sw-ink-muted` | `--sw-paper` | **6.65:1** | 4.5 | PASS | labels and timestamps |
| `--sw-pine` | `--sw-paper` | **5.94:1** | 4.5 | PASS | links and accent text |
| `--sw-on-pine` | `--sw-pine` | **6.53:1** | 4.5 | PASS | text on a primary button |
| `--sw-on-pine` | `--sw-danger` | **6.54:1** | 4.5 | PASS | text on a destructive button |
| `--sw-border-strong` | `--sw-paper` | **4.15:1** | 3.0 | PASS | table rules and strong hairlines |

**All pairs pass, in both themes: light 26/26 (tightest 3.08:1, the Uncategorised band), dark 26/26
(tightest 5.71:1, border-strong on paper).**

`--sw-ink-faint` is deliberately absent from that table. It is for placeholder and disabled
text only, where WCAG exempts the requirement. **It must never carry content.**

### §2.2 — The eight seeded categories

Ruled by `SW-ADR-092`. Measured against `--sw-paper` `#f7f4ec` (light; dark figures are in `CONTRAST.md`, lowest 6.88:1); the floor is 3:1 because a
band is a UI component, not text.

| Category | Token value | Measured vs paper | |
|---|---|---|---|
| Groceries | `#4a7c59` | **4.42:1** | PASS |
| Food & Dining | `#b5543b` | **4.45:1** | PASS |
| Transport | `#3e6b8f` | **5.16:1** | PASS |
| Rent & Utilities | `#9c7a2f` | **3.65:1** | PASS |
| Health | `#2e7d8a` | **4.33:1** | PASS |
| Entertainment | `#7b4b94` | **5.83:1** | PASS |
| Shopping | `#a04c72` | **5.07:1** | PASS |
| Other | `#7d8471` | **3.53:1** | PASS |
| Uncategorised | `#928a85` | **3.08:1** | PASS |

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
> **`--sw-cat-uncat` currently has the least headroom of any pair in the system, at +0.09. Any
> future change to `--sw-paper` breaks it first.**
>
> **2026-10-18 (liquid glass).** It nearly broke a fourth time. The audit's proposed paper `#f5efe6`
> put Uncategorised at **2.96:1**. The band could not move, because three artifacts must agree on
> its hex (`consistency_check.py band-colour-agreement`), so the paper moved instead, to `#f8f4ed`
> (3.09:1). The warmer sand lives only in `--sw-bg-2/3` as `background-image`, where no band is ever
> drawn. On the content-tier card (`#fffcf7`) Uncategorised measures 3.31:1. On `--sw-paper-sunken` it
> measures 2.86:1, **so a band is never drawn on a sunken well in light.** The audit's proposed
> darker hexes for cat-4, cat-8 and uncat (`#86671f`, `#687060`, `#7a726d`) were NOT adopted. They are
> an `SW-ADR-092` matter and need a recorded ruling, and they are not needed while bands sit on
> paper or a raised surface.
>
> **2026-10-18 (b, new money).** The owner's ivory `#f7f4ec` was checked BEFORE it was adopted:
> Uncategorised **3.08:1** (+0.08), so it stands. On light `--sw-paper-sunken` (`#efeadd`) it is
> 2.82:1 and on light chrome glass, worst case, 2.72:1. A swatch drawn on either therefore wears the
> `.sw-coin` / `.sw-swatch` rim (`--sw-border-strong`, 3.80:1 on sunken), which is what makes the
> component identifiable. A bare band is still never drawn there.

---

### §2.3 — Two tiers of glass

`SW-ADR-154` and `test_text_stays_readable_on_the_card_in_both_themes` require `.card`'s computed
background alpha to be **1**. A translucent card, or a transparent card with the glass painted on
`::before`, fails it. The test is not weakened. The system has two tiers instead:

| Tier | Classes | Surface |
|---|---|---|
| **Content**: solid glass | `.card` `.entries` `.table-wrap` `.state` `.sw-bankcard-solid` | opaque `--sw-paper-raised` + `--sw-highlight` (the inner 1px light edge) + layered `--sw-shadow-md` + optional TiltCard glare. Reads as glass and is opaque. |
| **Chrome**: real glass | `.glass` `.glass-thin` `.glass-thick` `.rail` `.topbar-mobile` `.gate-card` `.panel` `.periods` `.filters` `.segmented` `.tabs` `.btn-quiet` `.banner` `.toast` `.sw-bankcard` (decorative hero card) | translucent `--sw-glass*` + `backdrop-filter: blur() saturate()` + top sheen (light only). |

**Real money figures go on an opaque face.** The dashboard's total sits on `.sw-bankcard-solid`; the
translucent `.sw-bankcard` is for the login hero, where it carries only a wordmark, a masked number and
a name.

This matches the liquid-glass guidance the system was drawn from: glass on navigation and controls,
with content on its own layer. Making content cards translucent would need an ADR amending
`SW-ADR-154` and a human-approved test change. That is a reserved decision and is not taken here.

Fallbacks: `@supports not (backdrop-filter)`, `prefers-reduced-transparency: reduce` and
`prefers-contrast: more` turn every chrome surface into `--sw-glass-solid` (= the raised surface,
opaque). `prefers-contrast: more` also draws every edge in `--sw-border-strong`. Every figure can
only rise.

### §2.4 — Worst case over the guilloché and the orb (computed)

`contrast.py` composites glass over paper. What actually sits under the chrome is gradient stop →
guilloché lines (`--sw-guilloche` at its opacity) → the liquid orb (at `--sw-orb-opacity`) → glass.
These figures take the **minimum** over 24 composites per surface: every gradient stop × with and
without the guilloché × no orb or each pure orb stop. The orb shader writes only convex mixes of
its three stops, so luminance is extremal at the stops. The light top-sheen (white 0.30) is
included. **No credit is taken for blur.** The scripts are scratch tools for this revision
(`money_palette.py`, `final_check.py`); folding them into `tools/contrast.py` is outstanding work.

| Theme | Surface | ink | ink-muted | pine | gold | positive | warning | danger | border-strong (3:1) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dark (orb @0.42) | `--sw-glass` | 10.36 | 5.72 | 6.56 | 7.25 | 7.04 | 6.53 | 5.19 | 3.58 |
| | `--sw-glass-strong` | 12.96 | 7.16 | 8.20 | 9.07 | 8.81 | 8.17 | 6.50 | 4.48 |
| | sunken on glass | 13.77 | 7.60 | 8.71 | 9.63 | 9.35 | 8.67 | 6.90 | 4.76 |
| light (orb @0.40) | `--sw-glass` | 13.68 | 5.86 | 5.23 | 5.21 | 5.23 | 5.11 | 5.24 | 3.66 |
| | `--sw-glass-strong` | 15.08 | 6.46 | 5.77 | 5.74 | 5.77 | 5.63 | 5.77 | 4.03 |
| | sunken on glass | 14.11 | 6.04 | 5.39 | 5.37 | 5.39 | 5.27 | 5.40 | 3.77 |

**The bank card**, worst case including the orb behind it, its own guilloché rosette and the
metallic glare at full strength:

| Card | ink | muted | gold | positive | negative |
|---|---:|---:|---:|---:|---:|
| `.sw-bankcard` glass, dark (`--sw-card-glass` .58) | 6.83 | 4.69 | 4.77 | — | — |
| `.sw-bankcard` glass, light (.55) | 10.77 | 4.61 | 5.17 | — | — |
| `.sw-bankcard-solid`, both themes (lighter face stop `#0e3226`) | 7.29 | 5.01 | 5.10 | 5.32 | 4.75 |

These tables tuned the following values; none was chosen by eye:
- Light gold text went from `#8a6516` (4.26 on glass) to **`#7a5810`** (5.21). The light
  glass-card wordmark gold went to **`#674a0a`**, because at `#7a5810` the card's own guilloché
  pulled it to 4.10.
- Dark border-strong went from `#5e8a77` (3.03 on glass) to **`#6a9783`** (3.58).
- The solid card's second face stop was `#123a2b`, where muted measured 4.23 and negative 3.70.
- **A re-run is needed after raising `--sw-orb-opacity` or either guilloché opacity, or after
  lowering any `--sw-glass*` or `--sw-card-glass` alpha.**

Buttons, with the emerald→gold sheen (both stops at `--sw-sheen-alpha` 0.18 over the fill):

| | plain | worst with sheen | hover (`pine-deep`) with sheen |
|---|---:|---:|---:|
| light `--sw-on-pine` on `--sw-pine` | 6.53 | 5.16 | 6.64 |
| dark `--sw-on-pine` on `--sw-pine` | 10.49 | 10.38 | 12.18 |
| `--sw-on-gold` on `--sw-gold-fill` (`.btn-gold`), light / dark | 10.72 / 11.31 | 10.10 / 10.79 | — |
| `--sw-on-pine` on `--sw-danger` (no sheen), light / dark | 6.54 / 8.31 | — | — |

Soft pills, light / dark: pine on pine-soft 5.45 / 7.49; gold on gold-soft 5.38 / 9.47; danger on
danger-soft 5.23 / 6.95. The coin rim (`--sw-border-strong`) on `--sw-paper-sunken`: 3.80 / 5.87.

---

## §3 — Type

Liquid-glass revision: **one family**, Geist. It is variable (wght 100–900), from the official
release `vercel/geist-font` v1.8.1, licensed under the SIL OFL 1.1. It is self-hosted as
`client/public/fonts/Geist-Variable.woff2`, with `OFL-geist.txt` beside it. The release's
`Geist[wght].ttf` was checked with a cmap/GSUB reader: **U+20B9 ₹ present, `tnum` present**. The
woff2 is the same release's web build. In the browser, `document.fonts.check('16px Geist', '₹')` is
`true` and the face reports `loaded` (vite preview, 2026-10-18). The face is preloaded in
`index.html`. Bricolage Grotesque, DM Sans and JetBrains Mono are no longer referenced by any token.
Their files remain in `public/fonts/` until the legacy CSS is cleaned up, and nothing requests them.

| Step | Token | Size | Leading | Tracking | Weight | Use |
|---|---|---|---|---|---|---|
| xs | `--sw-text-xs` | 0.75rem | 1.4 | +0.01em | 500 | meta, axis, table head, pills |
| sm | `--sw-text-sm` | 0.8125rem | 1.3 | 0 | 500 | labels, in sentence case |
| base | `--sw-text-base` | 1rem | 1.5 | 0 | 400 | body |
| md | `--sw-text-md` | 1.125rem | | | 500 | |
| lg | `--sw-text-lg` | 1.375rem | 1.1 | -0.02em | 600 | card values, state titles |
| xl | `--sw-text-xl` | 1.75rem | 1.1 | -0.02em | 600 | section titles; page titles at phone width |
| 2xl | `--sw-text-2xl` | 2.25rem | 1.1 | -0.035em | 600 | page titles |
| 3xl | `--sw-text-3xl` | clamp(2.75rem, 6vw, 4.5rem) | 1.0 | -0.035em | 600 | the hero total |

Nothing is set below 12px. Nothing is uppercased. There is no `// ` prefix, and no mono "terminal"
label anywhere. Titles use `text-wrap: balance`. **Every number is tabular**: `.sw-num`, and every
numeric class in glass.css, sets `font-variant-numeric: tabular-nums`. `--sw-font-mono` keeps its
name for `.sw-num` and resolves to Geist.

Money is formatted `en-IN`, as ₹12,34,567.89 (`SW-ADR-056`), by `lib/money.js` and nothing else.

---

## §4 — Space, radius, shadow, motion

- **Space (4pt).** `--sw-space-1 2 3 4 5 6 8 10 12 14 20` = 4 8 12 16 20 24 32 40 48 56 80px.
- **Radius.** `--sw-radius-sm` 10px (inputs, chips), `-md` 14 (wells, banners), `-lg` 20 (cards),
  `-xl` 28 (gate card, panel), `-full` (pills). Inner radius = outer minus padding.
- **Shadow.** Every shadow has an offset and a soft blur, tinted from the warm ground (light) or ink
  (dark): `--sw-shadow-sm` / `-md` / `-lg` / `-panel`, plus `--sw-shadow-pine` under the primary
  button. `--sw-highlight` is the inner light edge every glass surface wears.
- **Blur.** `--sw-blur-sm` 8px (chips, segmented, quiet buttons), `-md` 20 (rail, top bar, toasts),
  `-lg` 32 (gate card, panel). `--sw-glass-saturate` 160% light / 140% dark. The scrim blurs 6px.

**Motion.** Curves come from the animate skill's table, not from approximations:
- `--sw-ease-out` `cubic-bezier(0.23, 1, 0.32, 1)`
- `--sw-ease-in-out` `(0.77, 0, 0.175, 1)`
- `--sw-ease-drawer` `(0.32, 0.72, 0, 1)`
- `--sw-ease-exit` `(0.4, 0, 1, 1)`, for exits only

`--sw-spring` is a `linear()` **computed** from a damped oscillator (Apple parameters duration 0.5s,
bounce 0.25, sampled over 650ms). It peaks at 1.028 and settles to 1.0005. Use it with
`--sw-dur-spring`.

Durations: press 120 · hover 180 · small 240 · enter 320 · route 400 · hero 450 · spring 650 ·
count 900 · roll 520 ms. The guilloché drifts one tile per 90s (`--sw-dur-drift`). The stagger is 40ms per item, capped at 8. Exits run at about 0.7× their entry.
Legacy `--sw-motion-fast/base/ease` remain and point at the same values.

**Under `prefers-reduced-motion: reduce`, motion is instant** (`SW-ADR-117`, unchanged):
- tokens.css collapses every duration;
- motion.css also removes stagger delays;
- CountUp shows the final value;
- TiltCard is inert;
- LiquidBlob draws one still frame;
- the guilloché and the rosette stop drifting, and Odometer reels jump to the new value.

These three were observed in a browser with reduced motion emulated: no `data-counting`,
`animation-name: none`, opacity 1. The LiquidBlob still frame is unverified; only the canvas being
present was checked.

---


## §5 — Components, with all five states

Every component specifies default · hover · focus · disabled · error/empty.

### Button
| State | Treatment |
|---|---|
| default | `--sw-pine` (emerald) fill, `--sw-on-pine` text, `--sw-radius-full` pill, emerald→gold sheen at `--sw-sheen-alpha` |
| hover | `--sw-pine-deep` fill; the sheen slides (transform), fine pointers only |
| press | `scale(0.97)` over `--sw-dur-press` |
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
Card `--sw-paper-raised` (opaque, §2.3) with `--sw-highlight` + `--sw-shadow-md`, `--sw-radius-lg`.
Table rows separate with `--sw-border`, never with fill striping. Chips (the period picker) sit in a
glass track; the active one (`aria-pressed`) is a raised knob. The panel is a real dialog — focus trapped on open, focus restored on close,
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

**Dark is not an inversion, and it is the primary design.** It has a deep forest ground
`#06140f`, an emerald accent `#3fd9a2` (10.46:1 on paper), champagne gold `#e8c77a`, mint positive,
amber warning, coral danger and ivory ink. Each value was chosen by running the tools until it passed
both `CONTRAST.md` and the §2.4 worst case. The nine category bands keep their `SW-ADR-147` dark
tints, lowest 6.88:1 on the new ground.

**"Dark first" is a design priority, not a default.** A person with no system preference still gets
light. The theme mechanism is unchanged: `SW-ADR-147 B`, `lib/theme.js`, and the test that "System"
means the attribute is absent. Making dark the default for "System" would be a behaviour change, so it
is not taken here.

**Glass composites, so its alpha is a measured floor.** The colour a person reads through glass is
`surface × α + backdrop × (1−α)`, and since 2026-10-18 the backdrop includes the guilloché and a moving
orb. The alphas below are the ones §2.4 measured:

| Token | Light | Dark | Use |
|---|---|---|---|
| `--sw-glass` | `rgb(255 253 247 / .70)` | `rgb(14 36 28 / .70)` | rail, top bar, chips, segmented, tabs |
| `--sw-glass-strong` | `/ .84` | `rgb(11 30 23 / .84)` | gate card, panel, toast, quiet buttons, banners |
| `--sw-glass-sunken` | `rgb(239 234 221 / .80)` | `rgb(3 12 9 / .45)` | wells and inputs |
| `--sw-glass-solid` | `#fffdf8` | `#0f2119` | the opaque fallback |
| `--sw-card-glass` | `rgb(255 253 247 / .55)` | `rgb(10 30 23 / .58)` | the decorative glass bank card |
| `--sw-glass-edge` | `rgb(40 52 30 / .12)` | `rgb(0 0 0 / .45)` | the outer hairline |
| `--sw-highlight` | inset white .80 top + .40 ring | warm .10 top + gold .07 ring | the inner light edge |
| `--sw-glass-sheen` | white .30 → 0 over the top 42% | `none` | the top-lit sheen |

`backdrop-filter` is **progressive enhancement**. Where it is unsupported, or under
`prefers-reduced-transparency` or `prefers-contrast: more`, the glass becomes `--sw-glass-solid` and
every figure rises.

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

---

## §9 — Contract for screen stylesheets (new money, 2026-10-18)

### 9.1 Files, order, ownership

`main.jsx` imports, in this order:
1. `tokens.css` (generated: edit `docs/05 B DesignSystem/tokens.css`, then `py client/sync_tokens.py`
   and `py tools/contrast.py`)
2. legacy `app.css`, `app.redesign.css`, `app.swiss.css` (dead rules, removed by a later cleanup)
3. **`glass.css`**: surfaces, primitives, money typography, the bank card, the guilloché
4. **`motion.css`**: keyframes, entrances, CountUp and Odometer styles
5. `screens/shell.css`, `screens/dashboard.css`, `screens/expenses.css`, `screens/settings-admin.css`

Screen sheets load last, so they win by order. Rules for every sheet:
- no `!important`;
- no raw hex (`npm run lint:tokens`);
- no `:focus-visible` rule (the ONE rule is in tokens.css);
- no `outline: none`;
- no `text-transform` on `.btn` or `.entry-meta`;
- **no violet, purple or pink**, and no new colour without a token and a contrast run.

To beat a legacy compound selector, repeat that exact selector in your sheet rather than raising
specificity.

**Surfaces belong to glass.css; geometry belongs to your sheet.** Do not restate `background`,
`backdrop-filter`, `border`, `box-shadow` or `border-radius` on `.rail`, `.topbar-mobile`,
`.gate-card`, `.panel`, `.card` or `.sw-bankcard`. Re-tint chrome with
`--glass-bg: var(--sw-glass-strong)` and `--glass-blur: var(--sw-blur-lg)`. Set width, height,
padding, position, grid and gap freely.

### 9.2 Hard constraints the browser tests read

- `.card` background must stay opaque (alpha 1) in both themes. `.card`, `.entries`, `.table-wrap`
  and `.state` use `--sw-paper-raised`, never `--sw-glass*`. The translucent `.sw-bankcard` must
  **not** also carry `.card`. The dashboard total uses `.sw-bankcard-solid`.
- `body` keeps an opaque `background-color: var(--sw-paper)`, darker in dark.
- No horizontal overflow at 375px. `.periods` and `.filters` keep `width: fit-content;
  max-width: 100%`. Put the orb, rosette and bank card inside `.sw-stage`, which clips sideways.
- The ribbon: no geometry changes (SW-ADR-055). `.band` keeps its opacity dim and its inset
  `box-shadow` selection cue. Never give `.band` or `.ribbon` an entrance with `fill-mode: both` or
  `forwards`. Never draw a bare band on light `--sw-paper-sunken` or glass; use `.sw-swatch`.
- Text read by tests (`total`, `stat-*`, `whoami`, button labels) must be the real final string at
  all times. `<CountUp>`, `<Odometer>` and `<Money>` all guarantee this (9.6).
- 44px minimum hit target (`--sw-target-min`) on every control.
- Neither `.app` nor `.gate` may get `transform`, `filter`, `opacity < 1`, `isolation` or a
  `z-index`. That would trap the backdrop layers (guilloché -4, vignette -3, orb -2, grain -1) in
  front of the content.

### 9.3 Custom properties (all `--sw-*`, both themes)

| Group | Names |
|---|---|
| Surfaces | `--sw-paper` `--sw-paper-raised` `--sw-paper-sunken` `--sw-glass` `--sw-glass-strong` `--sw-glass-sunken` `--sw-glass-solid` `--sw-glass-edge` `--sw-glass-border` `--sw-glass-sheen` `--sw-highlight` `--sw-scrim` |
| Ink and state | `--sw-ink` `--sw-ink-muted` `--sw-ink-faint` (placeholder/disabled only) `--sw-pine` (emerald) `--sw-pine-deep` `--sw-pine-soft` `--sw-on-pine` `--sw-positive` `--sw-warning` `--sw-danger` `--sw-danger-soft` `--sw-border` `--sw-border-strong` `--sw-focus-*` |
| Gold | `--sw-gold` (TEXT) `--sw-gold-fill` `--sw-gold-deep` `--sw-gold-soft` `--sw-on-gold` |
| Categories | `--sw-cat-1` … `--sw-cat-8` `--sw-cat-uncat` (unchanged, SW-ADR-092) |
| Bank card | `--sw-card-face-1/2` `--sw-card-ink` `--sw-card-muted` `--sw-card-gold` `--sw-card-positive` `--sw-card-negative` `--sw-card-glass` `--sw-card-glass-ink/-muted/-gold` `--sw-radius-card` `--sw-shadow-card` `--sw-foil` |
| Decoration | `--sw-orb-deep/-emerald/-gold` `--sw-orb-opacity` (legacy alias `--sw-blob-opacity`) `--sw-sheen-a/-b` `--sw-sheen-alpha` (cap 0.18) `--sw-specular` `--sw-glare` `--sw-wash-1/2` `--sw-bg-1/2/3` `--sw-grain*` |
| Guilloché | `--sw-guilloche` (fill colour) `--sw-guilloche-opacity` `--sw-guilloche-card-opacity`; the generated masks `--sw-guilloche-waves` (360×180 seamless tile) and `--sw-guilloche-rosette` (glass.css) |
| Type | `--sw-font-body/display/mono` (all Geist) `--sw-text-xs/sm/base/md/lg/xl/2xl/3xl/hero` `--sw-weight-regular/medium/semibold/bold` `--sw-leading-tight/snug/normal` `--sw-track-tight/display/caps` (caps = the card wordmark only) |
| Space | `--sw-space-1 2 3 4 5 6 8 10 12 14 20` |
| Radius | `--sw-radius-sm` (10) `-md` (14) `-lg` (20) `-card` (22) `-xl` (28) `-full` |
| Shadow | `--sw-shadow-sm/md/lg/panel/pine/card` |
| Blur | `--sw-blur-sm/md/lg` `--sw-glass-saturate` |
| Motion | `--sw-ease-out` `--sw-ease-in-out` `--sw-ease-drawer` `--sw-ease-exit` `--sw-spring` `--sw-dur-press/hover/small/enter/route/hero/spring/count/roll/drift` `--sw-stagger` |
| Charts | `--sw-plot-line` (emerald series) `--sw-plot-fill` `--sw-plot-gold` (highlight/comparison series) `--sw-plot-grid`; categories keep `--sw-cat-*` |
| Layers | `--sw-z-content` (1) `--sw-z-topbar` (30) `--sw-z-rail` (40) `--sw-z-scrim` (50) `--sw-z-overlay` (60) `--sw-z-toast` (70) `--sw-z-skip` (100) |

**Colour semantics, everywhere:** emerald (`--sw-pine`/`--sw-positive`) means income, under budget,
or the primary action. Gold (`--sw-gold`) marks totals, highlights and premium detail. Ink is
ordinary spending, which is normal and not an error. Coral (`--sw-danger`) is ONLY overspend or a
destructive action. Colour is never the only cue: pair it with a sign (+) or a word.

### 9.4 Classes provided by glass.css

**Backdrop** (no markup needed): `.app::before` / `.gate::before` draw the drifting guilloché waves,
and `::after` the still vignette. `body::after` is the grain. `body` carries the emerald/gold washes
and the gradient.
- `.sw-stage`: the hero wrapper. Positioned, clips sideways, centres its content and sets
  `perspective: 1200px`. Put `<LiquidBlob contained>`, an optional `.sw-rosette` and the
  `<BankCard>` in it, and give it an explicit `min-height` in your sheet.
- `.sw-rosette`: an empty, `aria-hidden` element that draws a turning guilloché rosette. Inside
  `.sw-stage` it is absolute and sized `min(130%, 640px)`.
- `.sw-guilloche`: an absolute wave band that fills its positioned parent (a card header, a strip).
  Content above it needs `position: relative`.

**Surfaces**
- `.glass` regular, `.glass-thin` small blur, `.glass-thick` strong. These are chrome.
- `.card` is the opaque content card. `.card-statement` adds a gold hairline across its top, like a
  bank statement's letterhead rule. Use it on the dashboard's statement cards.
- `.well` is a sunken inset.
- `.rail`, `.topbar-mobile`, `.gate-card` and `.panel` already wear chrome glass. The gate card and
  panel wear the thick level.

**The bank card**: render it with `<BankCard>` (9.7). The class map, if you hand-write it:
`.sw-bankcard` (glass) or `.sw-bankcard.sw-bankcard-solid` (opaque metal), with parts
`-guilloche -foil -top -brand -contactless -chip -body -label -value -number -bottom -holder -meta`.
It has ISO 7810 proportions, `max-width: 440px`, and is a size container. Set its width from your
sheet; never its padding.

**Money**
- `.sw-money` (tabular lining figures, nowrap). The parts are `.sw-money-cur` (₹) and
  `.sw-money-frac` (paise), produced by `<Money>`, `<CountUp>` and `<Odometer>`.
- **Display sizes only**: inside `.sw-total`, `.sw-bankcard-value`, `.card-hero-value` or
  `.sw-money-lg`, the ₹ is set lighter and raised and the paise become a superscript. At body size
  both stay plain (the 12px floor).
- `.sw-total` is THE big number, one per screen (`--sw-text-hero`). `.sw-total-gold` makes it gold.
- `.sw-pos` (emerald), `.sw-neg` (ink), `.sw-over` (coral), `.sw-gold`. On a bank card `.sw-pos` and
  `.sw-over` switch to the card-safe tints automatically.

**Ledger** (receipt-style lists)
- `ul.sw-ledger > li.sw-ledger-row`, a two-column grid: `.sw-ledger-main` (`.sw-ledger-title`,
  `.sw-ledger-meta`) and `.sw-ledger-amount`, which is right-aligned and tabular. Rows are 56px
  minimum with hairline rules.
- `.sw-leader`: label … dotted leader … figure (the last child).

**Categories as coins**
- `<span class="sw-coin" style={{'--coin': 'var(--sw-cat-3)'}}>Transport</span>` is a minted coin
  swatch with its name.
- `.sw-swatch` is the bare 18px coin (set `--coin`).
- The rim is `--sw-border-strong`. It is what keeps Uncategorised identifiable on glass.

**Buttons** (pill, 44px)
- `.btn` is the primary: emerald with an emerald→gold sheen that slides on hover, `scale(0.97)` on
  press.
- `.btn-gold` is the premium call to action, at most one per screen.
- `.btn-quiet` is a glass pill.
- `.btn-danger` is solid coral with no sheen.
- `.btn-danger-quiet` is outlined coral, for the reversible one of two consequences.
- `.btn-link`.
- `.icon-btn` is a 44px circle, with inline SVG at 20px and `stroke="currentColor"`.
- Sizes: `.btn-sm` (36px on desktop, 44px at ≤900px), `.btn-lg` (52px), `.btn-block`.
- Disabled is `aria-disabled="true"` or `:disabled`.

**Track and knob controls**
- The tracks are `.periods`, `.filters`, `.segmented` and `.tabs`.
- The items are `.chip[aria-pressed]`, `.segment[aria-checked]` and `.tab[aria-selected]`. The
  selected item is a raised knob.
- `.chip-accent[aria-pressed=true]` is an emerald knob. `.segmented-wide` spans the full width.

**Switch**: `<button class="switch" role="switch" aria-checked>Label</button>`. The track is emerald
when on, and the knob moves on `--sw-spring`.

**Inputs**
- `.field label` + `input`/`select`, `.row-form input`, `.field-grow input`, or `.sw-input` on any
  new field. All are sunken. On focus they switch to the raised surface with an emerald halo.
- `.sw-input-amount` (and `.panel input[name=amount]`) set the amount in big tabular figures, like
  writing a cheque.
- `aria-invalid="true"` gives a coral border. `.field-error` carries the message.

**Status and feedback**
- `.pill` (emerald), `.pill-gold` and `.pill-danger` are status labels, not buttons.
- `.banner` is a glass strip with a warning dot.
- `.form-error` is coral on danger-soft.
- `.notice`.
- `.skeleton` shimmers.
- `.state` and `.state-error`.

**Toasts**: one `<div class="toast-region" role="status" aria-live="polite">` holds
`<div class="toast">` children. Entry is automatic. To exit, set `data-leaving` and unmount after
`--sw-dur-small`. `.toast-positive` adds an emerald dot; `.toast-danger` colours the text coral.

**Type**: `.page-title` 2xl, `.section-title` xl, `.state-title` lg, `.panel-title` lg,
`.card-label`/`.card-heading` sm, `.card-value` lg, `.card-hero-value` 3xl, `.sw-total` hero. Also
`.sw-eyebrow` (gold, sm) and `.sw-lede` (md, muted, 34ch). Everything is in sentence case.

**Overlay**: `.scrim` with `.panel`. The panel's geometry belongs to the expenses sheet.

### 9.5 Classes provided by motion.css

| Class | Does | Notes |
|---|---|---|
| `.sw-route` | fade-through with a 3px blur and a 6px rise, 400ms | or use `<RouteFade viewKey>` (9.6) |
| `.sw-enter` | rise and fade, 320ms | `--sw-delay` offsets it |
| `.sw-pop` | scale 0.96→1 and fade, 240ms | |
| `.sw-grow` | `scaleX` from the left edge, 450ms | bars and meters, never `.band` |
| `.sw-stagger` | staggers its DIRECT children by 40ms, capped at 8 | |
| `.sw-press` | `scale(0.97)` on `:active` | custom pressables |
| `.sw-lift` | rises 2px with shadow-lg on hover | fine pointers only |

All entrances use `fill-mode: backwards` and are removed under reduced motion. Never animate a
keyboard-initiated action.

### 9.6 JS: `src/lib/motion.js`

- `usePrefersReducedMotion()` and `useFinePointer()` are live booleans. `prefersReducedMotion()` is
  the non-hook form.
- `staggerStyle(i, max = 8)` returns `{ '--sw-delay': … }` for `.sw-enter`/`.sw-pop` items that are
  not direct children.
- `tokenMs('--sw-dur-count', 900)` reads a duration token in ms.
- `splitMoney("₹7,581.00")` returns `{ sign, cur, int, frac }`, or `null` for non-money strings.
- `<Money paise={758100} />` renders a styled figure. Alternatives: `text="₹…"` for an
  already-formatted string, or `sign` to prefix "+" on a positive amount (income). Extra props go on
  the root.
- `<CountUp value={paise} className="sw-total" data-testid="total" />`
  - `format` defaults to `rupees`. Pass `split={false}` for a non-money figure, with its own
    `format`.
  - It counts from the on-screen value to the new one: expo ease-out, 900ms, resumable.
  - It does not count under reduced motion or in a hidden tab.
  - `innerText` is always the final string (observed in the specimen: the ticker showed ₹7,533.99
    while `innerText` read ₹7,581.00).
- `<Odometer value={paise} className="card-value" />` rolls each digit reel to its new value when
  `value` changes, right to left, 18ms apart, 520ms. Nothing rolls on first render. The real string
  is a visually hidden text node, which is the `innerText` and the accessible name; the reels are
  `aria-hidden`.
  - Use CountUp for the one hero total's entrance and Odometer for figures that change in place
    (a filter or period change).
- `<RouteFade viewKey={view}>…</RouteFade>` remounts and crossfades its pane.
- `useCountUp(rootRef, tickerRef, value, opts)` is the hook form. Copy CountUp's DOM shape: the
  ticker has three empty spans `.sw-money-cur`, plain, `.sw-money-frac`.

### 9.7 `<TiltCard>` and `<BankCard>` (`src/components/TiltCard.jsx`)

`import TiltCard, { BankCard } from '../components/TiltCard.jsx'`

`<TiltCard as="div" max={6} glare lift={1.01} className="…">`
- Pointer tilt reaches at most `max`° under `perspective(1000px)`. Moves follow on a 180ms ease-out
  transition (interruptible), and on leave it returns on `--sw-spring`. A specular glare follows the
  cursor.
- It is inert on touch, on coarse pointers, under reduced motion and from the keyboard, and it never
  changes layout or focus order. While tilted it is a stacking context, so no `position: fixed`
  children.
- Use it on one hero surface per screen, never on a chart someone is reading.

`<BankCard … />` is the SpendWise card: chip, contactless mark, SPENDWISE wordmark, masked number,
guilloché rosette and gold-foil edge. It tilts by default with a gold metallic glare.

| Prop | Default | |
|---|---|---|
| `variant` | `'glass'` | `'glass'` is translucent CHROME, for the login hero. `'solid'` is the opaque emerald metal face, **required whenever real money is on it**. |
| `label` | — | small muted line above `value` |
| `value` | — | the big figure node: `<CountUp>`, `<Odometer>` or `<Money>` |
| `children` | — | extra body content under `value` |
| `last4` / `number` | `'2026'` / `•••• •••• •••• {last4}` | masked number, shown only when there is no `value` |
| `holder` | — | bottom-left (the person's display name, or a placeholder) |
| `meta` | — | bottom-right small text (e.g. the period, "Since 2026") |
| `brand` | `'SPENDWISE'` | wordmark, gold, caps-tracked |
| `chip` | only when there is no `value` | the EMV chip |
| `decorative` | `false` | `aria-hidden` on the whole card. Use it on the login hero, where it repeats nothing a reader needs. |
| `tilt` / `max` | `true` / `6` | |
| `as`, `className`, rest | | passed to the root (e.g. `data-testid`) |

Recipes:
```jsx
// Gate (left column)
<div className="sw-stage gate-hero">
  <LiquidBlob contained x={0.55} y={0.5} size={0.8} />
  <span className="sw-rosette" aria-hidden="true" />
  <BankCard decorative holder="Your name" meta="Since 2026" />
</div>

// Dashboard hero (keep the existing test ids)
<div className="sw-stage dash-hero">
  <LiquidBlob contained x={0.6} y={0.45} size={0.85} />
  <BankCard variant="solid" data-testid="headline" label="Spent this month"
    value={<CountUp value={summary.total_paise} data-testid="total" />}
    holder={me.display_name} meta={periodLabel} />
</div>
```

### 9.8 `<LiquidBlob>` (`src/components/LiquidBlob.jsx`)

`<LiquidBlob contained x={0.55} y={0.5} size={0.8} />`

- A molten emerald→gold orb whose surface ripples like water. It is a WebGL1 shader at half
  resolution and 30fps, and a pointer move drops a ripple into it (`ripple={false}` turns that off).
- It pauses off screen and in a hidden tab, and draws one still frame under reduced motion. Without
  WebGL, or after a lost context, it is a still CSS orb from the same tokens.
- `contained` makes it absolute inside its positioned parent. Use that, inside `.sw-stage`, directly
  behind the bank card. Without `contained` it is fixed behind the page at z -2.
- **At most one per screen**: one on the gate and one on the dashboard hero. Other panes omit it.
- Do not override the wrapper's opacity. Contrast was measured at `--sw-orb-opacity` (§2.4).

### 9.9 Assets — which goes where

| Asset | Where | How |
|---|---|---|
| guilloché waves + rosette | everywhere | **Generated**, not downloaded: two SVG masks embedded in glass.css (≈18.7KB, no colour). Geometry: a hypotrochoid R100/r36/d52 in two phases plus 3 modulated rings, and 2×10 crossing amplitude-modulated sine lines in a seamless 360×180 tile. The generator script was a session scratch file and is **not in the repo**; committing it under `tools/` is outstanding. |
| `grain-256.webp` | everywhere | `body::after`, tiled, 5% soft-light (light) / 6% overlay (dark) |
| `liquid-violet-*`, `pearl-holo-*`, `ink-lightwave-*`, `liquid-chrome-*` | **retired** | Violet or iridescent; nothing references them. They remain in `client/public/assets/bg/` until their owner deletes them, and are served only if requested. |
| `ink-blobs-*` | **retired** | Amber and teal; nothing references it. |

No photo sits behind any text. Credits for the remaining files are in
`client/public/assets/bg/CREDITS.md`.

### 9.10 Icons

Replace the Unicode glyphs `◧ ◔ ⚙ ⚿ ☰ ✕` with inline SVG: 24 viewBox, 1.75 stroke,
`stroke-linecap="round"`, `fill="none" stroke="currentColor"`, drawn by hand in the JSX. No icon
library (SW-ADR-016). Size them 20px inside `.icon-btn` or `.rail-item`. The contactless mark in
`TiltCard.jsx` follows the same rules.
