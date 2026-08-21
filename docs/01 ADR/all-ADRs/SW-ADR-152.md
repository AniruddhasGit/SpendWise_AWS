# SW-ADR-152 — The palette and type pairing change; the token names do not

| Field | Value |
|---|---|
| ADR | `SW-ADR-152` |
| Pack | `SPENDWISE_V1` |
| Type | DESIGN_SYSTEM |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `CR-002` |
| Decided by | CLIENT (instruction 2026-08-21) · implemented by BUILD_SESSION |
| Decision date | 2026-08-21 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CR-002` · `SRC-001 §9.4` (reversed in part) · `SW-ADR-092` · `SW-ADR-117` · `SW-ADR-131` · `SW-ADR-147` · `SW-ADR-020` |

## Context

The client supplied a design handoff bundle reversing the visual half of `SRC-001 §9.4`: the
paper-and-pine palette becomes greenish-white / olive / near-black, and the Instrument Serif /
Instrument Sans / IBM Plex Mono pairing becomes Bricolage Grotesque / DM Sans / JetBrains Mono.

`SRC-001` is fingerprinted, so the clause is reversed by `CR-002` rather than edited. The
accessibility half of the same sentence — tabular figures, phone width, visible focus, reduced
motion — is untouched and still binding.

## Options considered

- **A.** Re-skin by editing components. Rejected: `npm run lint:tokens` forbids a raw hex in a
  component, and the change would have touched every `.jsx` file.
- **B.** Swap the token *values*, keep the token *names*, add one additive stylesheet.
- **C.** B, plus rename `--sw-pine` to something hue-neutral like `--sw-accent`.

## Decision

**B.** The token names are unchanged. `--sw-pine` still means "the accent" and now holds an olive.

C was rejected despite being the more honest name. `--sw-pine` is referenced across `app.css`,
`DESIGN-SYSTEM.md`, the contrast tool's pair table and several ADRs; renaming it would have turned
a theming change into a rename touching every one of those, for a gain that is entirely cosmetic in
the source. **The name is a slot, not a description of its contents.** This is recorded so a future
reader who finds `--sw-pine: #4e5f22` and assumes a mistake finds the reason instead.

Consequence of B, and the whole point of it: **zero `.jsx` files were edited.** The change is one
replaced token file, one added stylesheet imported after `app.css`, and one `<meta>` attribute.

## What changed

**Colour.** Light: `paper #f2f5e9`, `paper-raised #fbfcf6`, `paper-sunken #eaefdc`, `ink #14170e`,
`ink-muted #4f5643`, `ink-faint #7c8468`, `pine #4e5f22`, `pine-deep #354115`, `pine-soft #e2eaca`,
`border #d8e0c2`, `border-strong #7f8a63`, `on-pine #f7faee`. Dark is a re-tone, not an inversion
(`SW-ADR-147` holds): the accent becomes `#b8d16b` on a `#0d0f09` ground, because olive `#4e5f22`
measures far under 3:1 on near-black.

**Type.** Display `Bricolage Grotesque`, body `DM Sans`, mono `JetBrains Mono`. `--sw-text-2xl`
2rem → 2.5rem, `--sw-text-3xl` 2.75rem → 3.75rem, `--sw-leading-tight` 1.2 → 1.08.

**Geometry and motion.** Radii 3/6/10px → 5/10/14px. Shadows re-tinted to the new ink. Easing
`cubic-bezier(0.4, 0, 0.2, 1)` → `cubic-bezier(0.2, 0.8, 0.2, 1)`.

**`--sw-cat-uncat` `#948c87` → `#928a85`.** See below. Every other band hue is unchanged.

## Why the one band moved — the finding that justifies this record

The handoff specified the nine category bands as **unchanged** and listed them under *do not
change*. After the swap, `tools/contrast.py` failed exactly one pair:

```
light: --sw-cat-uncat on --sw-paper = 2.99:1, needs 3.0 (category band)
```

**The band did not change; the ground under it did.** `#948c87` measures 3.51:1 on the old paper
`#faf7f2` and 2.99:1 on the new `#f2f5e9`. A palette decision that never mentioned category bands
silently re-opened all nine, because a contrast pair has two sides and moving either one
invalidates every figure that rested on it.

Darkened within the hue to `#928a85` — **3.07:1**, hue drift `0.00°`, saturation drift `0.10pp`,
lightness `−0.78pp` — following the instruction `SW-ADR-092` gives for bands and the precedent
`SW-ADR-131` set for this exact token. `#938b86` also cleared the floor, at 3.029:1, and was
rejected: shipping 0.029 above a floor is the mistake `SW-ADR-147` is a record of.

**`--sw-cat-uncat` now has the least headroom in the system at +0.07.** Any future change to
`--sw-paper` breaks it first.

## The band colour lives in three artifacts

Darkening the token was not sufficient and no gate said so. The ribbon and donut render
`b.color` from the summary response, so the rendered colour is `UNCATEGORISED_COLOR` in
`app/modules/expenses/summary.py`; `contract.json` holds a third copy. `tools/contrast.py` reads
the stylesheet, and would have certified 3.07:1 for a hex the browser never drew.

All three now hold `#928a85`, and `consistency_check.py` gained a **`band-colour-agreement`**
check that fails unless they agree — red-proofed against the exact divergence, taking the selftest
to 17/17. A gate proves a property of the artifact it reads; this colour had three artifacts and
one reader.

## The fonts were never loaded, and now are

`SW-ADR-020` rejected a CDN for the frontend, so the families were always to be self-hosted. Until
this record there was **no `@font-face` rule and no font file under `client/`** — the families were
named and never fetched, and the app rendered system fallbacks throughout, including in every
screenshot under `evidence/`.

Three families now ship as six woff2 files (168 KB total) under `client/public/fonts/`, declared in
`app.redesign.css`. **Two subsets per family, not one:** `U+20B9` (₹) is in `latin-ext`, not
`latin`. A latin-only build — which is what the handoff's snippet specifies — would have rendered
every rupee sign from a fallback font beside digits from JetBrains Mono, in an application about
columns of money. Ranges are Google's own, read off the source CSS.

## Why

The instruction is the client's and the visual half of `§9.4` is theirs to reverse. What is **not**
reversible by instruction is `SW-ADR-117`'s accessibility floor: a palette that fails a floor is
not shipped prettier, it is adjusted until it measures. `CONSTITUTION.md` reserves waiving a
quality check to a human signature, and no such waiver was sought or needed — the floor was met by
moving a colour 0.8pp, not by lowering the bar.

## Consequences

- `DESIGN-SYSTEM.md` §2, §2.1, §2.2, §3, §4 now describe values that were **measured after the
  change**, not carried over. `CONTRAST.md` is regenerated by the tool.
- `SRC-001 §9.4`'s palette and font sentences are historical. The clause stays in the frozen file;
  `§1` of the design system quotes it verbatim with a pointer to `CR-002`.
- Screenshots under `evidence/` predating 2026-08-21 show neither this palette nor any of the
  intended typefaces.
- `pytest tests/browser` has **not** been run against this change — no Python 3.12 or `.env` exists
  on the machine that made it. Reasoned-not-observed, and recorded as such.

## Reversibility

**Yes, cheaply** — restore the previous `docs/05 B DesignSystem/tokens.css`, delete
`app.redesign.css` and its import, re-run `py client/sync_tokens.py` and `py tools/contrast.py`.
Nothing in `app/`, no migration and no `.jsx` file participates in this decision, which is the
property option B was chosen for.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file.*
