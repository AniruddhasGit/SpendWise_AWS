# SW-ADR-158 — The reel's motion: a staggered blur-in, a liquid theme flood, a fuller tree

> **⚠ AMENDED 2026-10-20 by `SW-ADR-159`.** The landing's sun, orbits and bright atmosphere are
> replaced by a gloomy dusk with ground mist. The blur-in and the theme flood stand.

| Field | Value |
|---|---|
| ADR | `SW-ADR-158` |
| Pack | `SPENDWISE_V1` |
| Type | DESIGN_SYSTEM |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instructions 2026-10-20 |
| Decision date | 2026-10-20 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Amends | `SW-ADR-156` (the tree's leaves, its falling bills, the landing atmosphere) |
| Sources | the owner's reference reel (code.xr "Dashboard V14", instagram.com/reel/DeoxA_vzRbo) · `SW-ADR-016` · `SW-ADR-117` · `SW-ADR-156` |

## Context

The owner sent a reel and asked for "transitions that look exactly like this since the start of the
page to everything". Read frame by frame, it does two things:

- **A staggered blur-in** (also called a focus-in reveal). Every piece of a screen starts transparent
  and out of focus and sharpens into place, in reading order, about 70ms apart. It plays on first
  load and again on every screen change. The shell (the bar and the rail) stays still and only the
  content arrives. There is no slide and no wipe.
- **A liquid theme flood.** Switching to dark grows a blob of the dark theme from the toggle that
  was pressed. Its front ripples like poured ink, and it covers the screen in under a second.

The reel's author used Framer Motion. `SW-ADR-016` locks the stack to plain CSS with no UI
framework, and neither move needs one.

The same day the owner also asked for:
- a fuller canopy, "about a 7 or 8" on their 1 to 10 scale;
- falling bills that stay one colour with red text, and are no bigger than the leaves;
- a visible atmosphere around the landing tree.

## Decision

1. **Every entrance is a blur-in.** `sw-rise` (used by `.sw-enter` and `.sw-stagger`) animates
   opacity, `filter: blur(14px)` to none, and a 10px rise. It never scales, so a 44px target
   measures 44px on every frame. A new `.sw-focus` utility orders hero pieces by `--sw-i`:
   - the landing bar, the headline group by group, the tree, the statement line by line, the action;
   - the dashboard head, tree, total, comparison, button and statement card;
   - the rail.

   Tokens: the new `--sw-dur-reveal` (620ms) times every arrival and the new `--sw-dur-focus` (760ms) each hero piece; `--sw-dur-enter` stays 320ms for drawers and sheets, which move rather than arrive, and
   `--sw-stagger` 40ms becomes 70ms. The fill mode stays `backwards`, so no filter outlives its
   animation.
2. **The theme flood** (`switchTheme` in `lib/theme.js`) uses the View Transitions API. The new
   theme's snapshot is clipped by a rippling closed curve around the pointer, which grows past the
   farthest corner in 950ms. The switch is instant when:
   - the browser lacks the API;
   - motion is reduced;
   - the press came from a keyboard (keyboard actions are never animated here);
   - nothing visible changes.

   The choice is saved before the animation starts.
3. **Reduced motion is still instant** (`SW-ADR-117`): `.sw-focus` joins the list that drops
   animation, and the theme switches with no flood.
4. **The tree.**
   - The canopy has 82 more banknote leaves, 137 in all. Each is a copy of a bill already painted in
     the artwork, placed on thin twigs only and never over the trunk or main limbs. This was done
     locally with no new generation and no Runway credits; the provenance is beside the image.
   - Falling bills use one sprite (the reverse side is removed, so a bill never changes colour as it
     turns) and are drawn at leaf size.
   - The landing adds drifting motes, a halftone vermilion sun behind the canopy, a third orbit and
     two more sparks. Mist and orbit lines are stronger. (Superseded the same day by `SW-ADR-159`:
     the owner rejected the sun and the bright atmosphere for a gloomy scene.)

## Judgment calls (`SW-ADR-015`)

- **[JUDGMENT CALL] One browser test waits for the theme.** A flood applies the theme on the next
  frame rather than inside the click. `test_the_choice_survives_a_reload_and_system_is_the_absence_of_it`
  now polls for the attribute before the unchanged assertion that it is absent. Nothing was removed
  or loosened.
- **[JUDGMENT CALL] Page changes have no exit animation.** The reel clears the old content at once
  and blurs the new content in, and that is what this does. No view transition was added to
  navigation, so the pointer is never blocked between screens.
- **[JUDGMENT CALL] Bills are leaf-sized, with a legibility floor.** A bill is 5.6% of the tree's
  width, but never below 60% of its former 62 by 32px, so its amount can still be read.
