# SW-ADR-154 — The surface goes flat: readability is measured, not achieved by glass

| Field | Value |
|---|---|
| ADR | `SW-ADR-154` |
| Pack | `SPENDWISE_V1` |
| Type | DESIGN_SYSTEM |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instruction 2026-08-27 |
| Decision date | 2026-08-27 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Amends | `SW-ADR-147` **D** · the browser criterion in `tests/browser/test_the_shell.py` |
| Sources | `SW-ADR-147` · `SW-ADR-152` · `CONSTITUTION.md` Art II.1, Art IX.2 · the client's Swiss restyle handoff |

## Context

The client supplied a third visual revision — a Swiss / International-style restyle that keeps every
colour where `SW-ADR-152` put it and changes only the **surface language**: hairline rules instead of
cards, no shadows, square corners, oversized display type, mono uppercase micro-labels.

Part of that language is a **flat ground**. The restyle sets `--sw-glass` to `--sw-paper`,
`--sw-glass-blur` to `0`, and every glass alpha to `1`.

`SW-ADR-147` **D** had ruled the opposite, and ruled it for a good reason:

> **Glass alpha is a measured floor, not a taste.** `--sw-glass` is `rgb(255 255 255 / 0.78)`
> because that is where `--sw-ink-muted` on glass still clears 4.5:1 over the pine wash.

A browser criterion enforced it directly:

```python
assert "rgba" in style["bg"], f"{theme}: the card is not translucent ({style['bg']})"
```

Applying the restyle turned that criterion red. **It could not be made green by fixing the code** —
the restyle removes translucency deliberately, so satisfying the assertion would have meant
abandoning the restyle. Two approved intentions, directly opposed.

Under `CONSTITUTION.md` Art IX.2 the build session does not edit a test to reach green, and under
Art II.1 a client ruling outranks an APPROVED ADR. The contradiction was surfaced with three
options and stopped. The client chose **A**.

## Decision

**The ground is flat. Readability is asserted by measuring it.**

1. `--sw-glass`, `--sw-glass-strong` and `--sw-glass-sunken` resolve to opaque paper tokens;
   `--sw-glass-blur` is `0`. Surfaces separate with a `1px --sw-border` hairline.
2. The browser criterion is rewritten from *"the card is translucent"* to *"body ink on the card
   clears 4.5:1, and the surface it is painted on is unblended."*
3. **`SW-ADR-147` D is amended, not withdrawn.** Its principle — that a contrast floor is computed
   and not asserted — is untouched and is now enforced more directly. Only its *mechanism* clause,
   which pinned the floor to a specific alpha, no longer applies.

## Why the replacement criterion is stronger, not weaker

This matters, because rewriting a criterion to match what was built is the failure mode
`SW-ADR-153` exists to prevent. The distinction:

| | Old criterion | New criterion |
|---|---|---|
| What it asserted | the background string contains `rgba` | the painted ink-on-card ratio ≥ 4.5:1 |
| Computes a ratio | **no** | yes, WCAG 2.1 relative luminance, in the browser |
| Catches an unreadable card | **no** — a translucent card compositing to mud passed | yes |
| Catches a translucent card | yes | yes — reported separately, so a regression says which assumption broke |

The old assertion checked **how** readability was achieved. The new one checks **that** it is
achieved, and additionally keeps the flat-ground guarantee `contrast.py`'s figures now depend on.
Every case the old criterion caught is still caught.

## Evidence

- `tools/contrast.py`: **light 26/26 pass · dark 26/26 pass** against the restyled tokens. The
  glass alphas going to 1 means every composited pair becomes its own unblended pair, which can
  only measure higher.
- `npm run lint:tokens`: PASS — 25 client files, no raw hex, one focus rule, no `outline: none`.
- The new criterion was **red-proofed both ways** before being trusted:
  - card forced translucent → `light: the card is translucent (rgba(120, 140, 90, 0.5))`
  - card forced opaque but low-contrast → `light: body ink on the card is 3.46:1, below the 4.5:1 floor`
  - reverted, green again.

## Consequences

- `docs/05 B DesignSystem/CONTRAST.md` regenerates; the row `--sw-ink` on `--sw-glass` now measures
  an unblended pair.
- **No `.jsx` file changed for the restyle itself.** Every change is CSS on class names that already
  existed. (Two `.jsx` files did change in the same session, for the sign-out relocation — unrelated
  to this ADR.)
- Token **names** are unchanged. `--sw-pine` still means "the accent".
- The restyle shipped with two defects of its own, found by the browser suite and fixed rather than
  ruled around — recorded here because they were part of the same drop:
  - `.periods` carried `width: max-content`, which defeated `app.css`'s `flex-wrap: wrap` and pushed
    the page **222px past a 375px window**. Now `fit-content` + `max-width: 100%`.
  - `.entry-meta` had been added to the mono-uppercase label list, but it is not a label class: it
    renders a person's own category name, their email address in the rail and the admin table, the
    `days-elapsed` figure the day-one gate reads, and every chart caption. An address stored as
    `a@spendwise.test` was displayed as `A@SPENDWISE.TEST`. Removed from that list. Six browser
    criteria caught it, including `CV-16`'s.
