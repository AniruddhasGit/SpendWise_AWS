# SW-ADR-147 — Two themes, glass surfaces, and contrast that is computed for all of them

> **⚠ AMENDED 2026-08-27 by `SW-ADR-154`.**
> Clause **D** below — *"glass alpha is a measured floor, not a taste"* — pinned the floor to a
> specific alpha (`0.78`). The client's Swiss restyle sets every glass alpha to `1` and the blur to
> `0`, because a ruled grid needs a flat ground. **The principle is untouched and is now enforced
> more directly**: the browser criterion no longer asks whether the surface is translucent, it
> measures the ink-on-card ratio the browser actually painted and requires 4.5:1 — which the old
> assertion never computed at all. Read clause D as "the floor is measured, never asserted"; do not
> read it as "the surface must be translucent". Everything else in this record stands, including the
> two themes, the appearance control, and contrast being computed for both.

| Field | Value |
|---|---|
| ADR | `SW-ADR-147` |
| Pack | `SPENDWISE_V1` |
| Type | UX |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Amends | — |
| Amended by | `SW-ADR-154` (clause D, 2026-08-27) |
| Raised by | Client request, 2026-08-06: a sidebar shell, an appearance control, and "a greenish glassmorphism going on" |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-06 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §9.4` · `SW-ADR-092` · `SW-ADR-117` · `SW-ADR-131` · WCAG 2.1 SC 1.4.3, SC 1.4.11 |

## Context

`DESIGN-SYSTEM.md` opens with a promise:

> Every contrast figure below was **computed** from the hex values in `tokens.css`, not
> asserted. The script is in the goal's evidence; re-run it rather than trusting this page.

That promise was kept by hand, once, for one opaque theme. The client has now asked for a dark
mode and for translucent surfaces, and **neither is hand-checkable**:

* A second theme doubles every pair and changes which ones are tight. Pine `#2d5a3d` is the
  accent at 7.44:1 on paper; on a dark surface the same hex measures **1.6:1**. Five of the nine
  category bands have the same problem.
* Glass **composites**. The colour a person actually reads is `surface × α + backdrop × (1−α)`,
  which is written down nowhere. A figure for `--sw-ink` on `--sw-glass` cannot be looked up; it
  has to be calculated, and it changes when the alpha changes.

So the promise had to become a program or be withdrawn.

## Decision

**A. `tools/contrast.py` computes every pair and is a gate.** WCAG 2.1 relative luminance,
source-over compositing for translucent surfaces, `var()` resolved so
`--sw-focus-color: var(--sw-pine)` is measured as the thing that renders. It emits
`docs/05 B DesignSystem/CONTRAST.md` and joins `consistency_check.py`'s generated-artifact list.

**It fails on a pair below its floor, not only on drift.** A generated table that faithfully
records a 2.36:1 would be a document doing its job while the product fails the standard it claims.

**B. Dark is declared twice, and that is not redundancy.** `@media (prefers-color-scheme: dark)`
is the default, so a person whose system is dark gets dark before any script runs and never sees a
white flash. `:root[data-theme="dark"]` is the override the appearance control writes. The media
query is scoped `:root:not([data-theme="light"])` so an explicit light choice beats a dark system.

**C. Dark is not an inversion.** Pine stays the accent at a lighter tint of the same hue
(`#7fc79a`), and five category bands are re-tinted. Every replacement was chosen by running the
tool until it passed.

**D. Glass alpha is a measured floor, not a taste.** `--sw-glass` is `rgb(255 255 255 / 0.78)`
because that is where `--sw-ink-muted` on glass still clears 4.5:1 over the pine wash. Lowering it
for a prettier blur is a change the gate refuses.

**E. `--sw-on-pine` is a token.** Text on a pine or danger fill was `--sw-paper` used
positionally in three components — correct, and invisible to a contrast table that only knows
about named pairs.

## The defect this found on its first honest run

`--sw-border-strong` was `#a8a29e`, which measures **2.36:1** against paper — below the 3:1 that
`DESIGN-SYSTEM.md §6` requires of a UI component, and the token's own stated use is *"focus-adjacent
borders, table rules"*.

`SW-ADR-131` measured **exactly that hex, found exactly that figure**, and darkened it — for the
*Uncategorised band*. The identical value sat in the identical file doing a job with the identical
floor, and was never re-checked, because the measurement was per-token and by hand: someone
listed the bands, measured the bands, fixed a band. Nothing listed the borders.

Darkened within the same hue to `#8a837b`, **3.50:1**.

Both themes now measure 26/26.

## Consequences

- The design system's opening promise is now enforced rather than asserted, and it covers pairs
  nobody thought to list — which is how the border was found.
- **A hand-maintained check measures what someone remembered.** `SW-ADR-131` is not a failure of
  care; it is the ceiling of care. The fix for that class is never more diligence.
- Twelve generated artifacts are now verified by regeneration on every run.
- The first version of the parser tracked a scope flag and flipped it on any line starting `:root`
  that did not contain "dark" — which is what `:root:not([data-theme="light"])`, the dark block's
  own selector, looks like. Every dark value landed in the light table and the two rendered
  tables came out **byte-identical**. It now raises if the themes resolve equal, because a
  checker that silently measures one theme twice is worse than no checker.

---

*Ruled under `SW-ADR-015`.*
