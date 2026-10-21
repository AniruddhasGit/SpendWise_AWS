# SW-ADR-156 — The Festival Poster: ivory, emerald, vermilion, and the money tree

> **⚠ AMENDED 2026-10-21 by `SW-ADR-160`:** the sign-in page joins the signed-out scene (dusk/dawn,
> the shared theme switch), and the tree is carried to it from the landing page.


> **⚠ AMENDED 2026-10-20 by `SW-ADR-159`.** The landing page is now a gloomy dusk scene: the tree
> centred on a glass floor, ground mist over everything, details below the fold.

> **⚠ AMENDED 2026-10-20 by `SW-ADR-158`.** The canopy is fuller (137 leaves), falling bills are
> one colour and leaf-sized, the landing atmosphere is stronger, and every entrance is the owner's
> reel's staggered blur-in.

| Field | Value |
|---|---|
| ADR | `SW-ADR-156` |
| Pack | `SPENDWISE_V1` |
| Type | DESIGN_SYSTEM |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instructions 2026-10-19 and 2026-10-20 |
| Decision date | 2026-10-20 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Amends | `SW-ADR-147` (sixth visual revision; the two-tier surface rule stands) · the sign-in helpers in `tests/browser/` |
| Sources | the owner's "Change of Perspective" poster reference · `PRODUCT.md` · `.impeccable/surfaces/client-src-screens-dashboard-jsx.md` · `SW-ADR-016` · `SW-ADR-092` · `SW-ADR-154` |

## Context

The owner replaced the emerald-and-gold "New Money" look with a palette taken from a festival poster
they supplied: **Warm Ivory `#F9EBD7`, Emerald Green `#046A38`, Vermilion `#E34222`**, with the poster's
extruded block lettering, risograph grain and thin orbit lines. They asked for glassmorphism in that
palette, and for a **money tree**: a bonsai whose leaves are banknotes, standing on a glass ground with
its roots fading out, dropping bills that say what was spent. They asked for a **landing page** in front
of the sign-in form, with Sign in at the top right and an atmosphere around the tree (breeze, ground
mist, the poster's orbits).

An earlier same-day attempt at "premium motion" (framer-motion, a coin loader, a cinematic login) was
rejected by the owner and reverted before release (`c331e94`); it never received a ledger row, so this
number is unused until now.

## Decision

1. **Palette.** Token values move; every token name is unchanged (`tools/contrast.py`,
   `consistency_check.py` and the components read them by name). Emerald is `--sw-pine`; vermilion is
   the second voice and is carried by the `--sw-gold*` names (money leaving: totals, falling bills,
   the projection). `--sw-danger` is a deeper vermilion that clears 4.5:1 for text. Both themes pass
   `contrast.py` 26/26.
2. **Type.** `--sw-font-display` is Big Shoulders Display (OFL, self-hosted under `client/public/fonts`).
   It has no rupee sign, so `₹` falls through to Geist on purpose. Body text stays Geist.
3. **The money tree** (`MoneyTree.jsx`): one still image (`/assets/tree/money-tree.webp`, generated
   with Runway and cleaned locally; provenance in the sidecar beside it) plus a canvas of falling bills.
   Bills are canvas pixels, never DOM text, so no figure a test or screen reader reads is ever
   mid-animation. Reduced motion draws nothing; off-screen and hidden tabs pause it.
4. **The front door.** A fresh visit opens on the landing page. Sign in and Create your account open the
   existing form. A sign-out, an ended session, or a reload of a tab that has held a session goes
   straight to the form, where the reason banner is.
5. **The dashboard hero** is the tree beside the total, set in extruded numerals on the page (real money
   is still never printed on translucent glass). The statement card is unchanged and is still the first
   `.card`, opaque (`SW-ADR-154`). The bank card and liquid orb leave the dashboard and the sign-in
   screen; their components remain for any screen that still uses them.
6. **No new dependency.** The tree is an image, a canvas and plain CSS. `SW-ADR-016` is untouched.

## Judgment calls (`SW-ADR-015`: decided, logged, reversible with one message)

- **[JUDGMENT CALL] Page paper is `#FBF0E0`, not `#F9EBD7`.** On the owner's exact ivory the frozen
  `--sw-cat-uncat` band (`SW-ADR-092`, and equal to the server's `UNCATEGORISED_COLOR`) measures
  2.89:1 against a 3:1 floor. Changing a frozen band or waiving the check are both reserved; lifting the
  page paper 2% is not. `#F9EBD7` itself is `--sw-bg-1`, the ground the backdrop paints, so the owner's
  colour is what the eye sees around every surface.
- **[JUDGMENT CALL] Constant brand inks.** `--sw-brand-ivory/emerald/vermilion` (+ deep variants) do not
  change with the theme. They are for printed objects only (a banknote is paper in either theme) and are
  never page text; the themed tokens keep the contrast guarantees.
- **[JUDGMENT CALL] A reload after a session goes to the form.** One bit in `sessionStorage`, per tab,
  nothing personal. Without it a revoked person reloading would land on the marketing page, which is
  the wrong answer and is what `test_the_shell.py`'s revoke test catches.
- **[JUDGMENT CALL] Example bills.** On the landing page (nobody signed in) and on a dashboard with no
  entries, bills carry illustrative spends (Pizza, Chai, Rent...). They are labels on a picture, never
  presented as anyone's figures.

## Tests

- The browser sign-in helpers (`_register`, `_sign_in` in `test_the_shell.py` and `test_the_website.py`)
  now pass through the landing page: one extra click on the landing page's own Sign in or Create your
  account. **No assertion was changed or removed.** Every criterion still runs against the same form.
- Added: `test_the_front_door_is_the_landing_page_and_sign_in_opens_the_form` and
  `test_the_landing_page_does_not_overflow_at_375px` (it counts what it examined before asserting that
  nothing crossed the edge).

## Consequences

- The design system's colour section, glass tiers and asset table describe the new values
  (`DESIGN-SYSTEM.md`), and `CONTRAST.md` is regenerated.
- The landing page is the public face of the showcase deployment.
