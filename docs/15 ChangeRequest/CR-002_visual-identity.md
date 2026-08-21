# CR-002 — The visual identity moves from paper-and-pine to olive on greenish-white

| Field | Value |
|---|---|
| Change request | `CR-002` |
| Raised by | **The client**, 2026-08-21, verbatim below |
| Status | **ACCEPTED** — implemented under `SW-ADR-152` |
| Reverses | `SRC-001 §9.4` (the palette sentence and the three named font families) |
| Amends | `SW-ADR-147` (dark-mode reasoning) · `SW-ADR-131` · `SW-ADR-092` (band floors, re-measured) |
| Does not touch | `SW-ADR-117` (the accessibility floor) · `SW-ADR-055` · `SW-ADR-109` · `SW-ADR-020` |

## What was asked for

> Also, before all that D:\SpendWise\SpendWise UI redesign use this design as the front end adjust
> if needed. this is a example of how i want my design to look like.

The request arrived as a **design handoff bundle** rather than as prose: a README specifying every
hex, font stack, radius, shadow and duration; two drop-in CSS files; and a standalone HTML
prototype of all seven screens. The bundle is preserved at `SpendWise UI redesign/` and is the
authority on intent for this change.

## Why this is a change request and not a restyle

`SRC-001` is fingerprinted and cannot be struck where it stands. The clause being reversed is the
client's own visual brief, quoted in `DESIGN-SYSTEM.md §1` as the whole of what the design system
was derived from:

> "Look and feel: **paper and pine green**, not the default blue SaaS dashboard. **Instrument
> Serif** for display, **Instrument Sans** for body, **IBM Plex Mono** for every number. Tabular
> figures so columns of money line up. Works down to phone width, keyboard focus visible, reduced
> motion respected." — `SRC-001 §9.4`

Three of those clauses are reversed and three survive:

| Clause | Fate |
|---|---|
| "paper and pine green" | **reversed** — greenish-white `#f2f5e9`, olive `#4e5f22`, near-black `#14170e` |
| "not the default blue SaaS dashboard" | **survives** — the replacement is further from it, not nearer |
| Instrument Serif / Instrument Sans / IBM Plex Mono | **reversed** — Bricolage Grotesque / DM Sans / JetBrains Mono |
| "tabular figures so columns of money line up" | **survives** — `.sw-num` unchanged, still mono, still `tnum` |
| "works down to phone width" | **survives** — no media query was touched |
| "keyboard focus visible, reduced motion respected" | **survives** — one `:focus-visible` rule, still in `tokens.css` |

The quote in `§1` is **left standing verbatim** and annotated with a pointer here. Editing it in
place would have destroyed the record of what was originally asked for, which is the same reason
`CR-001` exists as a file rather than as a diff.

## What was NOT changed, and why that mattered

The handoff's own "What NOT to change" list was followed:

- **No `.jsx` file was edited.** Zero. The whole change is a token swap plus one additive
  stylesheet, which is only possible because the token *names* were left alone — `--sw-pine` still
  means "the accent" and now holds an olive.
- The nine category band **hues** are unchanged (one had its tone adjusted — see below).
- `--sw-warning` and `--sw-danger` are unchanged. A warning that reads as the accent is not a
  warning.
- The ribbon's proportional geometry, roving tabindex and two selection cues; the two-summary
  rule; the dialog's focus trap and `inert` handling; the absence of a router.

## The one thing the handoff got wrong, and it was load-bearing

The bundle's README says, twice and in bold, that the **category bands are UNCHANGED**, and lists
them under *What NOT to change*. It also predicted which pair would be tightest:

> `--sw-border-strong` `#7f8a63` vs `--sw-paper` — needs ≥3:1 … **Aimed at ~3.3:1, so it has the
> least headroom of anything here.**

That prediction was correct about `border-strong` (measured **3.33:1**) and wrong about which pair
would fail. The failure was `--sw-cat-uncat` `#948c87` on the new paper, at **2.99:1** against a
3.0 floor — **a fail by 0.01**.

**The band did not change. The ground under it did.** `#948c87` measured 3.51:1 against the old
paper `#faf7f2` and 2.99:1 against the new `#f2f5e9`. Every "unchanged" band silently had its
contrast re-opened by a decision that never mentioned bands, because *a contrast pair is a pair* —
changing either side re-opens every figure resting on it.

Resolved as `SW-ADR-092` instructs and `SW-ADR-131` set precedent for on this exact token: darkened
**within the hue** to `#928a85`, **3.07:1**. Hue drift `0.00°`, saturation drift `0.10pp`,
lightness `-0.78pp` — chosen by search over the neighbourhood for the candidate that preserved hue
exactly while clearing the floor with headroom. `#938b86` also cleared it at 3.029:1 and was
rejected: 0.029 above a floor is how `SW-ADR-147` happened.

This is the third time a token in this project has failed a floor because someone reasoned about
colour instead of measuring it (`SW-ADR-131`, `SW-ADR-147`, now this). The tool caught it in under
a second. **The estimate was the handoff's; the measurement is the record.**

## The second defect, caught by running it

The handoff's `@font-face` snippet specifies **one file per family**. Followed literally, that
ships the `latin` subset only — and `U+20B9`, the rupee sign, **is not in `latin`**. It is in
`latin-ext` (range `U+20AD-20C0`); `latin` carries `U+20AC`, the euro.

Every money figure in this product is `en-IN` formatted and begins with `₹`. A latin-only build
would have rendered the ₹ from a fallback font while the digits beside it came from JetBrains
Mono — in an application whose entire subject is columns of money.

Shipped with **two subsets per family**, unicode-ranges read off Google's own source CSS rather
than retyped. Verified in a real browser: with the faces force-loaded,
`document.fonts.check('500 16px "JetBrains Mono"', '₹')` returns `true`, and ₹ measures 20.00px in
JetBrains Mono against 21.99px in the fallback — a different glyph from a different file.

## The third defect — and the one that would have shipped

The band fix above was **incomplete for about twenty minutes, and every gate said otherwise.**

`--sw-cat-uncat` was darkened in `tokens.css`, `py tools/contrast.py --check` went green at
3.07:1, and the design system's §2.2 was regenerated to say so. All of that was true and none of
it was what the browser draws.

**The Uncategorised colour is a server value.** `Ribbon.jsx:119` and `Donut.jsx:51` paint
`background: b.color` inline from the summary response, and that colour originates in
`app/modules/expenses/summary.py` as `UNCATEGORISED_COLOR`. The CSS token is read only by
`Categories.jsx`'s swatch picker. So after the "fix":

| Artifact | Held | Rendered by |
|---|---|---|
| `--sw-cat-uncat` in `tokens.css` | `#928a85` | the swatch picker only |
| `UNCATEGORISED_COLOR` in `summary.py` | **`#948c87`** | **the ribbon and the donut** |
| `synthetic.color` in `contract.json` | `#948c87` | the API contract of record |

`tools/contrast.py` measures the stylesheet. It would have reported **PASS at 3.07:1 for a colour
the application never used**, while the ribbon drew the 2.99:1 value it was supposed to replace.
That is not a missing gate — it is a gate producing *evidence for the wrong artifact*, which is
strictly worse, because the output is a green tick with a number beside it.

Fixed in all three, plus the generated `expected_summary.json` and the day-one gate's own
assertion, and `generate_api.py` re-verified `daily_average_paise = 75810` through the change.

**The durable half:** `tools/consistency_check.py` gained a `band-colour-agreement` check that
reads all three sources and fails if they are not one hex. Red-proofed by planting the exact
divergence that existed here — the selftest is now **17/17**, up from 16.

Found by grepping for the old hex outside the stylesheet rather than by trusting three green
gates. The lesson is narrower than "test more": **a gate proves a property of the artifact it
reads.** Three artifacts held this colour and one tool read one of them.

## A standing fact this change corrected

`SW-ADR-020` rejected a font CDN, so the families were always meant to be self-hosted. **They never
were.** Before this change there was no `@font-face` rule and no font file anywhere under
`client/` — the three families were named in `tokens.css` and never loaded. Every screenshot under
`evidence/` predating 2026-08-21 shows the OS fallback, not the design that was signed off.

The handoff found this by reading the repository. It is recorded here rather than quietly fixed
because it means the design system was **unverified in the browser for its entire existence**, and
`§2.1`'s figures were true of hexes that were rendering in the right colours and the wrong
typefaces.

## Verification

| Gate | Result |
|---|---|
| `py tools/contrast.py --check` | **PASS** — light 26/26, dark 26/26 |
| `npm run lint:tokens` | **PASS** — 24 files, no raw hex, one focus rule |
| `py client/sync_tokens.py --check` | **PASS** |
| `npm run build` | **PASS** — 51 modules |
| Browser, both themes | light + dark rendered and screenshotted, `evidence/redesign/` |
| Fonts | all three families loaded from `client/public/fonts/`, ₹ confirmed from the real file |

`pytest tests/browser` is **NOT yet run** — this machine has no Python 3.12, no virtualenv and no
`.env`, so the suite cannot execute here. That is an environment gap, recorded as a gap. The
browser evidence above was gathered with Playwright driving the Vite dev server directly, which
proves the rendering and **does not** substitute for the 50 browser tests.

## Tightest margins after the change

| Pair | Measured | Floor | Margin |
|---|---|---|---|
| `cat-uncat` on `paper` | 3.07:1 | 3.0 | **+0.07** |
| `border-strong` on `paper` | 3.33:1 | 3.0 | +0.33 |
| `cat-8` on `paper` | 3.51:1 | 3.0 | +0.51 |
| `cat-4` on `paper` | 3.63:1 | 3.0 | +0.63 |
| `warning` on `paper` | 5.34:1 | 4.5 | +0.84 |

`cat-uncat` now has the least headroom in the system. **Any future change to `--sw-paper` breaks it
first** — which is the sentence that would have prevented this change request from having a defect
in it.
