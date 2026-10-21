---
name: SpendWise
description: A personal dollar expense tracker set as a festival poster for your month; ivory paper, emerald ink, vermilion for money leaving.
colors:
  paper: "#fbf0e0"
  paper-dark: "#0a1c13"
  bg-ivory: "#f9ebd7"
  bg-ivory-dark: "#0a1c13"
  paper-raised: "#fdf6ec"
  paper-raised-dark: "#10271b"
  paper-sunken: "#f2e1c7"
  paper-sunken-dark: "#07140d"
  ink: "#0b2a1c"
  ink-dark: "#f9ebd7"
  ink-muted: "#3c5446"
  ink-muted-dark: "#c4bba6"
  ink-faint: "#8b8a76"
  ink-faint-dark: "#7f8a7b"
  pine: "#046a38"
  pine-dark: "#5fd59a"
  pine-deep: "#03522b"
  pine-deep-dark: "#8ae6b6"
  pine-soft: "#e1e8cf"
  pine-soft-dark: "#12382a"
  on-pine: "#ffffff"
  on-pine-dark: "#06140d"
  positive: "#046a38"
  positive-dark: "#5fd59a"
  gold: "#b3301a"
  gold-dark: "#ff8f73"
  gold-fill: "#e34222"
  gold-deep: "#c4361a"
  gold-soft: "#fadccf"
  gold-soft-dark: "#3a1a12"
  on-gold: "#fffaf2"
  danger: "#b3301a"
  danger-dark: "#ff8466"
  danger-soft: "#f8d6c8"
  danger-soft-dark: "#3b1a12"
  warning: "#7f4a08"
  warning-dark: "#f2b657"
  border: "#e6d2b4"
  border-dark: "#1f3a2c"
  border-strong: "#7a6c52"
  border-strong-dark: "#7d9a87"
  extrude: "#0b2a1c"
  extrude-dark: "#046a38"
  glass: "rgb(253 246 236 / 0.62)"
  glass-dark: "rgb(16 40 28 / 0.66)"
  glass-strong: "rgb(253 246 236 / 0.82)"
  glass-strong-dark: "rgb(12 32 22 / 0.84)"
  glass-sunken: "rgb(242 225 199 / 0.70)"
  glass-sunken-dark: "rgb(4 14 9 / 0.45)"
  glass-solid: "#fdf6ec"
  glass-solid-dark: "#10271b"
  brand-ivory: "#f9ebd7"
  brand-emerald: "#046a38"
  brand-emerald-deep: "#03522b"
  brand-vermilion: "#e34222"
  brand-vermilion-deep: "#b3301a"
  plot-line: "#046a38"
  plot-line-dark: "#5fd59a"
  plot-gold: "#c4361a"
  plot-gold-dark: "#ff8f73"
  cat-1: "#4a7c59"
  cat-2: "#b5543b"
  cat-3: "#3e6b8f"
  cat-4: "#9c7a2f"
  cat-5: "#2e7d8a"
  cat-6: "#7b4b94"
  cat-7: "#a04c72"
  cat-8: "#7d8471"
  cat-uncat: "#928a85"
  cat-1-dark: "#6fae82"
  cat-2-dark: "#e08a6f"
  cat-3-dark: "#74a6cc"
  cat-4-dark: "#d4ae5e"
  cat-5-dark: "#62b8c4"
  cat-6-dark: "#b48ecb"
  cat-7-dark: "#d883a6"
  cat-8-dark: "#a8b09c"
  cat-uncat-dark: "#9aa096"
typography:
  display:
    fontFamily: "Big Shoulders Display, Geist, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "clamp(3rem, 8cqi, 5.5rem)"
    fontWeight: 900
    lineHeight: 0.95
    letterSpacing: "0.015em"
    fontFeature: "tnum, lnum"
  headline:
    fontFamily: "Big Shoulders Display, Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 4.4vw, 5rem)"
    fontWeight: 900
    lineHeight: 0.96
    letterSpacing: "0.015em"
  title:
    fontFamily: "Big Shoulders Display, Geist, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.6rem, 2.3vw, 2.25rem)"
    fontWeight: 800
    lineHeight: 1.02
    letterSpacing: "0.01em"
  figure:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
    fontFeature: "tnum, lnum"
  body:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Geist, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "normal"
rounded:
  sm: "10px"
  md: "14px"
  lg: "20px"
  card: "22px"
  xl: "28px"
  full: "999px"
spacing:
  "1": "0.25rem"
  "2": "0.5rem"
  "3": "0.75rem"
  "4": "1rem"
  "5": "1.25rem"
  "6": "1.5rem"
  "8": "2rem"
  "10": "2.5rem"
  "12": "3rem"
  "14": "3.5rem"
  "20": "5rem"
components:
  button-primary:
    backgroundColor: "{colors.pine}"
    textColor: "{colors.on-pine}"
    rounded: "{rounded.full}"
    padding: "0 1.25rem"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.pine-deep}"
    textColor: "{colors.on-pine}"
  button-primary-large:
    backgroundColor: "{colors.pine}"
    textColor: "{colors.on-pine}"
    rounded: "{rounded.full}"
    padding: "0 1.5rem"
    height: "52px"
  button-quiet:
    backgroundColor: "{colors.glass-strong}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    padding: "0 1.25rem"
    height: "44px"
  button-quiet-hover:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-pine}"
    rounded: "{rounded.full}"
    height: "44px"
  chip:
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.full}"
    padding: "0 1rem"
    height: "44px"
  chip-selected:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
  card:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "1.25rem"
  input:
    backgroundColor: "{colors.glass-sunken}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0 0.75rem"
    height: "44px"
  input-focus:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
  rail-item-selected:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    height: "44px"
  dashboard-total:
    textColor: "{colors.pine}"
    typography: "{typography.display}"
  entry-fresh-tag:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
    rounded: "{rounded.full}"
    padding: "0 0.5rem"
---

# Design System: SpendWise

## Overview

**Creative North Star: "The Festival Poster"**

SpendWise reads your month like a screen-printed festival poster. The headline act is the period total, set in chunky extruded emerald numerals; the centrepiece is the money tree, a risograph-print bonsai whose leaves are banknotes, dropping bills that say what was spent. Around them the sheet is warm ivory paper with fine grain, crossed by thin vermilion orbit lines and small four-point spark stars. The palette is the owner's own poster reference (SW-ADR-156): Warm Ivory, Emerald, Vermilion, and nothing else carries brand weight.

Density is calm in the poster band and ordinary below it. The first viewport is composed, not tiled: tree and headline share the space, then the screen settles into opaque paper cards for charts, the category ribbon and the entry list. Glass is the chrome, not the content: frosted ivory panes (night-green in the dark theme) hold the navigation rail, the top bar, the period track, the sign-in card and the tree's ground; every real figure sits on opaque paper or directly on the page.

The system is two-themed. Dark is primary in the token file's own words (a night-green sheet with ivory ink), light is the ivory poster; both carry measured contrast for every text pair. It is built in plain CSS on React with no UI framework (SW-ADR-016), every colour flows through a `--sw-*` custom property, and every contrast figure is computed by `tools/contrast.py` from token values, never by eye.

**Key Characteristics:**
- Emerald is the ink and the action; vermilion is money leaving; ivory is the paper.
- Display type is a condensed block face, extruded in a deeper green, uppercase only on poster lines.
- Two surface tiers: content opaque, chrome glass. Real money never sits on translucent glass.
- One signature object: the money tree, a still print plus a canvas of printed bills.
- Motion is decorative and ambient, never in the path of a figure; reduced motion is instant.

## Colors

A three-ink poster: ivory paper, emerald ink, vermilion accent, with deep emerald-black and night green carrying text and the dark sheet.

### Primary
- **Poster Emerald** (`--sw-pine`, `{colors.pine}` / `{colors.pine-dark}`): the accent. Primary buttons, links, the focus ring, selection, the dashboard total's face, the landing and gate headlines, the daily series in every chart. The token name is historical; it means "the accent".
- **Emerald Deep** (`--sw-pine-deep`): primary hover only.
- **Emerald Wash** (`--sw-pine-soft`): the focus halo on inputs and the selected legend row's field.

### Secondary
- **Vermilion** (carried by the `--sw-gold*` names): the second voice, money leaving. `--sw-gold` is vermilion *text* (the projection figure, the donut's centre total); `--sw-gold-fill` and `--sw-gold-deep` are vermilion *surfaces* (the wordmark coin, the statement card's top hairline, foil); `--sw-plot-gold` draws the running-total line and each chart's peak bead.
- **Poster Vermilion Statement** (`--sw-danger`, `{colors.danger}`): overspend, destructive actions and errors, and by the design system's own §2 table also the poster's condensed statement lines (the landing statement and the dashboard's total label). In light it is the same ink as vermilion text.

### Tertiary
- **Constant brand inks** (`--sw-brand-ivory`, `-emerald`, `-emerald-deep`, `-vermilion`, `-vermilion-deep`): identical in both themes, for printed objects only. The money tree's bills, its orbit ellipses and spark stars, and the dashboard's orbit arc and sparks use these, because a banknote is paper in either theme. Never page text.

### Neutral
- **Lifted Ivory Paper** (`--sw-paper`, `{colors.paper}`): the page ground. The owner's ivory lifted 2% so the frozen uncategorised band keeps 3:1 on it.
- **Owner's Ivory** (`--sw-bg-1`, `{colors.bg-ivory}`): the backdrop the page gradient starts from, with `--sw-bg-2` / `--sw-bg-3` as background-image stops only.
- **Raised Paper** (`--sw-paper-raised`): the content tier. Cards, the entry list, tables, state panels, selected knobs.
- **Sunken Paper** (`--sw-paper-sunken`): wells, coin chips, the ribbon track, disabled buttons.
- **Forest Ink** (`--sw-ink`): primary text. **Muted Ink** (`--sw-ink-muted`): labels, meta, unselected chips. **Faint Ink** (`--sw-ink-faint`): placeholder and disabled only, never content.
- **Hairline** (`--sw-border`) and **Rim** (`--sw-border-strong`, the 3:1 component border and the coin rim).
- **Category bands** (`--sw-cat-1` to `--sw-cat-8`, `--sw-cat-uncat`): frozen by SW-ADR-092; `--sw-cat-uncat` must equal the server's uncategorised colour.

### Named Rules
**The Three Inks Rule.** Emerald acts, vermilion spends, ivory holds. No violet, purple or pink anywhere; no fourth brand hue.

**The No Raw Hex Rule.** Components reference `--sw-*` tokens only; tokens hold the hex. `npm run lint:tokens` greps the client for a raw hex and fails the build. Edit `docs/05 B DesignSystem/tokens.css`, then regenerate `client/src/styles/tokens.css` with `py client/sync_tokens.py`; never edit the generated copy.

**The Measured Contrast Rule.** Every text pair is computed by `tools/contrast.py` from the token values (light 26/26, dark 26/26 at this revision). A value is never changed by eye; changing a glass alpha, the orb or guilloché opacity needs a re-run.

**The Printed Object Rule.** The `--sw-brand-*` inks are for printed things on the poster (bills, orbits, sparks). Themed tokens carry text and its guarantees.

## Typography

**Display Font:** Big Shoulders Display (variable 100 to 900, self-hosted, OFL), falling back to Geist, then system sans
**Body Font:** Geist (variable 100 to 900, self-hosted, full file including ₹ and `tnum`), falling back to system sans
**Numeric Font:** `--sw-font-mono` keeps its name for `.sw-num` but resolves to Geist with tabular figures

**Character:** A condensed poster block face for the few lines that shout, over a neutral, precise grotesque for everything that informs. Big Shoulders carries its own `$` (amounts are US dollars, `SW-ADR-157`); on the dashboard total it is set at weight 800 so it sits with the 900-weight digits.

### Hierarchy
- **Display** (Big Shoulders 900, clamp(3rem, 8cqi, 5.5rem), 0.95): the dashboard total only, extruded, emerald, tabular lining figures. At phone width clamp(2.5rem, 14cqi, 3.5rem).
- **Headline** (Big Shoulders 900, clamp(2.5rem, 4.4vw, 5rem), 0.96, uppercase): the landing headline and the gate title (clamp(2.5rem, 4.4vw, 3.75rem) there), extruded, emerald.
- **Title** (Big Shoulders 800, clamp(1.6rem, 2.3vw, 2.25rem), 1.02, uppercase): the landing's vermilion statement; the dashboard's total label uses the same face at `--sw-text-xl` (1.75rem). The wordmark uses the display face in sentence case.
- **Figure** (Geist 600, `--sw-text-2xl` 2.25rem, 1.1, -0.02em): statement-card values; tabular lining figures, always.
- **Body** (Geist 400, 1rem, 1.5): all running text.
- **Label** (Geist 500, `--sw-text-sm` 0.8125rem): chips, segmented controls, card labels, field errors, in sentence case.

The full step scale is `--sw-text-xs` 0.75rem, `-sm` 0.8125rem, `-base` 1rem, `-md` 1.125rem, `-lg` 1.375rem, `-xl` 1.75rem, `-2xl` 2.25rem, `-3xl` clamp(2.75rem, 6vw, 4.5rem), `-hero` clamp(3rem, 8vw, 5.75rem). Weights 400 / 500 / 600 / 700 tokens; the display face also uses 800 and 900 literally.

### Named Rules
**The Poster Voice Rule.** Big Shoulders and uppercase belong to poster lines only: the headline, the statement, the total and its label. Buttons, chips, entry metadata and every body line stay Geist in sentence case, never text-transformed.

**The Tabular Money Rule.** Every number uses tabular figures (`.sw-num`, and every numeric class). Money is formatted in US dollars, en-US ($1,234,567.89), by `lib/money.js` and nothing else (`SW-ADR-157`).

## Layout

A 4pt spacing scale (`--sw-space-1` to `--sw-space-20`: 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 80px). Targets are at least 44px (`--sw-target-min`) on every interactive control at phone width.

The **landing** sheet is a three-column poster grid (1.05fr headline, 1.7fr tree, 0.8fr statement and action, max 1440px), where the tree may spill past its column (width min(118%, 860px), -9% inline margin). Under 1100px it becomes headline and statement over a full-width tree; under 640px a single column: headline, tree, statement, full-width action.

The **dashboard** answers to its pane, not the window: `.dash-pane` is a size container, because the rail takes different room at each breakpoint. At 880px of pane and wider the hero is two columns (1.2fr tree, minmax(19rem, 1fr) poster) and the orbit arc and sparks appear; from 560px to 880px the hero stacks and the three statement figures sit in a row with hairline rules between; under 560px everything is one column and the tree shrinks to min(78%, 300px). Chart cards pair at 1.5fr / 1fr from 880px.

The **app shell** is a 16.5rem glass rail beside the content column; at 900px and below the rail becomes a drawer (transform on the drawer curve) behind a mobile glass top bar.

**The 375px Rule.** Nothing crosses the window edge at 375px: no sideways scroll and no box past the right edge, clipped or not. Decorative layers (the tree's glow, mist, orbits) are sized so they never widen the page; `overflow-x: hidden` on the body is never the fix.

## Elevation & Depth

A hybrid: soft offset shadows tinted from the forest ground, an inner 1px light edge on every glass and content surface, and real backdrop blur on the chrome tier. Depth reads as paper lifted off a sheet, not as floating material.

**The Two Tiers Rule.** CONTENT (`.card`, `.entries`, `.table-wrap`, `.state`, `.sw-bankcard-solid`) is opaque `--sw-paper-raised`; SW-ADR-154 and a browser test require the first `.card`'s computed background alpha to be 1. CHROME (`.glass`, `.rail`, `.topbar-mobile`, `.gate-card`, `.panel`, the period/filter/segmented/tab tracks, `.btn-quiet`, `.banner`, the landing bar, the tree's ground) is translucent `--sw-glass*` with `backdrop-filter: blur() saturate()`. Glass thicknesses: `--sw-blur-sm` 8px for tracks and quiet buttons, `-md` 20px for rail, bars and the tree pool, `-lg` 32px for the gate card and panel. Saturate is `--sw-glass-saturate` (150% light, 140% dark).

**The Opaque Fallback Rule.** Without backdrop-filter support, or under `prefers-reduced-transparency: reduce` or `prefers-contrast: more`, every chrome surface becomes `--sw-glass-solid`; under `prefers-contrast: more` every edge is drawn in `--sw-border-strong`. Contrast figures only rise. No credit is ever taken for blur.

### Shadow Vocabulary
- **Small** (`--sw-shadow-sm`): chips, tracks, quiet buttons, selected knobs.
- **Medium** (`--sw-shadow-md`): cards and default glass.
- **Large / Panel** (`--sw-shadow-lg`, `--sw-shadow-panel`): the gate card and the expense panel.
- **Emerald** (`--sw-shadow-pine`): under the primary button only; in dark it glows faintly emerald.
- **Card** (`--sw-shadow-card`): the bank card component.
- **Highlight** (`--sw-highlight`): the inset light edge every glass and content surface wears.

### Named Rules
**The Extrusion Is Lettering Rule.** The poster's hard offset depth lives on display type only (`.sw-extruded`), never on boxes, buttons or cards. Surfaces use the soft shadow vocabulary above.

## Shapes

Soft, pill-forward geometry under hard-edged lettering. Controls are full pills (`--sw-radius-full`); cards are gently rounded at 20px (`--sw-radius-lg`); the gate card and panel at 28px (`--sw-radius-xl`); inputs and chips' inner pieces at 10px (`--sw-radius-sm`); rail items and banners at 14px (`--sw-radius-md`). Inner radius equals outer minus padding; a track's radius is half a one-line height plus its padding, so a wrapped track becomes a soft rectangle, not a lozenge.

Recurring poster geometry: the **orbit** (thin ellipses or an open arc, 1.4 to 1.6px non-scaling stroke, some dashed `2 8` / `2 10`, in brand vermilion at 0.6 to 0.8 opacity), the **spark** (a four-point star with 0.18-radius waist, solid brand vermilion), the **coin** (a round category swatch with a 1px `--sw-border-strong` rim, which is what keeps a band legible on glass), and the **ground disc** (an elliptical frosted pool the tree's roots fade into).

## Components

### Buttons
Tactile emerald pills with a metal sheen.
- **Shape:** full pill (`{rounded.full}`), min height 44px; `.btn-lg` 52px, `.btn-sm` 36px (44px at 900px and below).
- **Primary:** `--sw-pine` fill, `--sw-on-pine` Geist 600 text, `--sw-highlight` plus `--sw-shadow-pine`. A `::before` sheen of `--sw-sheen-a` to `--sw-sheen-b` at `--sw-sheen-alpha` 0.18 (the cap; on-pine stays at or above 5.16:1).
- **Hover / Press:** on fine pointers the fill goes to `--sw-pine-deep` and the sheen slides by transform over `--sw-dur-hero`; press is `scale(0.97)` over `--sw-dur-press` 120ms. Disabled is `--sw-paper-sunken` with `--sw-ink-faint` and no sheen.
- **Quiet:** a glass pill (`--sw-glass-strong`, 8px blur) in ink; hover lifts to `--sw-paper-raised`.
- **Danger:** solid `--sw-danger`, no sheen ("metal is not for consequences"), always behind a confirm. `.btn-danger-quiet` is an outlined variant.
- **Link:** emerald, underlined 1px at 0.25em offset, 44px target.

### Chips, segmented controls and tabs
One track-and-knob language. The track is a glass pill (`--sw-glass`, 8px blur, `fit-content`, max-width 100%); items are transparent pills in muted ink; the selected item (`aria-pressed`, `aria-checked`, `aria-selected`) becomes a raised knob in `--sw-paper-raised` with ink, weight 600 and `--sw-shadow-sm`.

### Cards / Containers
- **Corner Style:** 20px (`{rounded.lg}`).
- **Background:** `--sw-paper-raised`, opaque, always.
- **Shadow Strategy:** `--sw-highlight` plus `--sw-shadow-md`; edge `--sw-glass-edge`.
- **Internal Padding:** `--sw-space-5` (20px).
- **Statement card:** `.card-statement` adds a 1px vermilion hairline across the top (gold-deep to gold-fill to gold-deep). The dashboard's three figures (entries, daily average, projection) read as lines of a bank statement in one such card, never three equal tiles.

### Inputs / Fields
- **Style:** 44px high, `--sw-glass-sunken` well, 1px `--sw-border`, 10px radius, inset shadow, Geist 1rem.
- **Focus:** border `--sw-pine`, background `--sw-paper-raised`, a 4px `--sw-pine-soft` halo, plus the global focus ring.
- **Error:** border `--sw-danger`, message below the field in `--sw-danger`, never a toast. The amount field is set large (`--sw-text-xl`, 600) with tabular figures.

### Navigation
The rail is chrome glass (16.5rem). Items are 44px rows, 14px radius, Geist 500 in muted ink; hover goes to `--sw-glass-sunken`; the current page is a raised knob in `--sw-paper-raised` with ink at 600 and an emerald icon. At 900px and below the rail is a drawer over a scrim, and a glass top bar carries the wordmark. The wordmark is the display face beside a vermilion coin (gold-fill to gold-deep gradient with a gold-soft inner ring).

### Extruded Lettering (`.sw-extruded`)
The poster's block-letter depth: five stacked `text-shadow` copies in `--sw-extrude`, offset 0.01em to 0.05em diagonally, plus one soft ambient shadow, with 0.015em tracking. Sized in em so depth scales with the type and the letters never smear. The glyphs stay real, selectable text, so a figure's `innerText` is always its final value. `--sw-extrude` is deep forest (`#0b2a1c`) in light and Poster Emerald in dark. Used on the landing headline, the gate title and the dashboard total.

### The Money Tree (`MoneyTree.jsx`, signature)
A risograph-print bonsai whose leaves are banknotes: one still image (`/assets/tree/money-tree.webp`, 1200px, provenance in its `.json` sidecar), standing on a frosted glass ground disc where its roots fade out (a mask from 76% to 96% of the height), with a soft glow pooled behind the canopy.
- **Bills are printed, not drawn.** One pre-rendered sprite (`bill-front.webp`, 256 by 132, generated locally with provenance beside it) carries the paper, guilloche, halftone oval and vermilion misregistration. Canvas only writes the label (Geist 700, brand vermilion deep) and the amount (Big Shoulders 900, brand vermilion) in its clear band. Every bill is 62 by 32px and the same ivory paper whatever it says, including the bill a new expense drops (the owner, 2026-10-20: no colour change while falling, no bigger bills). A bill flutters by a cosine tilt never thinner than 60%, never turning over, sways, and settles on the ground line, then fades.
- **What bills say.** On the dashboard, the person's own recent entries (category, or description, and amount); with nothing logged, and always on the landing page, labelled illustrative spends. Never anyone else's money.
- **Featured drop.** After the server confirms a new expense the dashboard sends one `dropRequest`; a bill at 2.2 times size leaves the top of the canopy carrying exactly that label and amount, falls slower, lingers on the ground about 2.2s, and lands with a burst of seven vermilion spark stars.
- **Rhythm.** A bill every 3.4s (dashboard, at most 18 live) or 1.9s (landing, at most 30). Brushing the pointer across the canopy shakes bills loose from the nearest leaves. The landing variant adds atmosphere: a breeze every 7 to 13s that sways the tree about its root and carries bills sideways, three drifting mist bands (28s, 34s, 41s), two slowly turning orbit ellipses (46s, 58s) and four twinkling sparks (5.5s).
- **Accessibility.** The canvas is `aria-hidden`; bills are pixels, never DOM text, so no figure a test or screen reader reads is ever mid-animation. It pauses off-screen and in hidden tabs, and re-reads its palette on theme change.
- **Reduced motion draws nothing.** No bills, no drop, no brush response; the tree holds still at rest. The still print remains.

### The Dashboard Poster Hero
The tree (left, on a feathered glass pool carrying the grain, never boxed as a card) beside the poster column: the total's label in condensed vermilion caps, the total in extruded emerald display numerals set on the page (never on glass), the comparison line with an arrow, number and words (less spending is emerald, more is plain ink, never coral), then the large "Add expense" pill, then the statement card. One dashed vermilion orbit arc leaves the canopy and lands beside the total, with two sparks, on wide panes only. Entrance is a staggered rise (`--sw-dur-hero` / `--sw-dur-enter`, `--sw-stagger` 40ms) that plays once per person; the total counts up from ₹0 on first view only. A just-added entry carries a small uppercase vermilion tag on `--sw-danger-soft` until it has been seen.

## Do's and Don'ts

### Do:
- **Do** take every colour from a `--sw-*` token, and change values only in `docs/05 B DesignSystem/tokens.css`, then regenerate the client copy and re-run `tools/contrast.py`.
- **Do** keep emerald for action and positive money, and vermilion (`--sw-gold*`, `--sw-plot-gold`) for money leaving: totals, projections, peaks, falling bills.
- **Do** put real figures on opaque paper (`--sw-paper-raised`) or directly on the page; keep glass for chrome.
- **Do** set the total and poster headlines in Big Shoulders Display with `.sw-extruded`, the `$` included.
- **Do** use tabular lining figures for every number and format money only through `lib/money.js`.
- **Do** carry the poster motif with the orbit line and the four-point spark in `--sw-brand-vermilion`, as decoration that is `aria-hidden` and hidden on narrow panes.
- **Do** make reduced motion instant: durations collapse, entrance animations are removed, and the money tree draws nothing.
- **Do** keep every interactive target at least 44px and every layout free of sideways scroll at 375px.

### Don't:
- **Don't** add a UI framework, component library or animation dependency; the stack is React with plain CSS (SW-ADR-016), and the tree is an image, a canvas and CSS.
- **Don't** write a raw hex in a component stylesheet or edit the generated `client/src/styles/tokens.css`.
- **Don't** make a content card translucent; the first `.card` must compute to alpha 1 (SW-ADR-154).
- **Don't** print the total or any real figure on translucent glass.
- **Don't** use `--sw-brand-*` inks for page text; they are for printed objects.
- **Don't** introduce violet, purple, pink or a fourth brand hue.
- **Don't** uppercase or switch to the display face for buttons, chips, labels or entry metadata.
- **Don't** put hard offset shadows on boxes; the extrusion belongs to lettering only.
- **Don't** paint a bare category band on sunken or glass surfaces; use the rimmed coin or swatch.
- **Don't** set `outline: none` or add a second `:focus-visible` rule; the one focus rule lives in tokens.css (SW-ADR-117).
- **Don't** render animated figures as DOM text mid-animation; moving money is canvas pixels, and readable figures are always final.
