# SW-ADR-159 — The landing scene: a gloomy dusk, a glass floor, ground mist

> **⚠ AMENDED 2026-10-21 by `SW-ADR-160`:** the landing's arrival is now a GSAP timeline after a
> wake-up countdown, the scene has a light (dawn) mode, and the fog and tree run whatever the motion
> preference, by the owner's ruling.


| Field | Value |
|---|---|
| ADR | `SW-ADR-159` |
| Pack | `SPENDWISE_V1` |
| Type | DESIGN_SYSTEM |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instructions 2026-10-20 |
| Decision date | 2026-10-20 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Amends | `SW-ADR-156` (the landing page's composition and atmosphere) · `SW-ADR-158` (the sun is removed) |
| Sources | owner instructions 2026-10-20 · `SW-ADR-016` · `SW-ADR-117` |

## Context

The owner rejected the bright poster atmosphere ("that fog and the sun") and asked for:
- a gloomy scene;
- mist that lurks on the ground and moves across the whole landing page, over the words too;
- the tree at the centre, with very little text either side;
- a glassy flat floor for proper grounding, seen from a raised camera. The owner's measure was a
  10cm tree shot from about 8cm up, "an elevation type", not straight down;
- generic details that appear as the page is scrolled.

## Decision

1. **Scene.**
   - The landing is an overcast dusk, the same in both themes, like the brand inks. It uses new
     constant tokens `--sw-dusk-*`.
   - The edges fall into a vignette. *(A pale fog glow behind the canopy was removed later on
     2026-10-20: the owner rejected it as a white halo around the tree.)*
   - Type is the dimmed ivory `--sw-dusk-ink`, well past 7:1 on the dark edges. The quiet line,
     `--sw-dusk-ink-quiet`, measures about 5.8:1 on `--sw-dusk-mid`.
2. **Composition.** Three columns: the headline (right-aligned, left of the tree), the tree, then
   one line and the action. On a phone they stack in one column.
3. **Floor.**
   - A frosted glass ellipse whose top edge is where the trunk enters it, so the roots are seen
     blurred through the glass.
   - It has a lit rim, a front lip for thickness, and the trunk mirrored faintly in it.
   - `--floor-ratio` sets the camera height. The owner compared samples at 4cm, 8cm and 14cm up on
     a 10cm tree and chose **14cm** (0.37: the floor dips about 22 degrees below the eye).
   - The tree picture itself stays side-on. Only the floor, reflection and shadow carry the camera
     height.
4. **Mist.**
   - `Fog.jsx` is a canvas of soft banks drawn at half resolution.
   - About 70% of the fog lies on the floor and the rest is thin wisps higher up. It drifts across
     the whole first screen, the words included.
   - One still frame under reduced motion. It pauses off screen.
   - **Revised by the owner later on 2026-10-20**, from two reference pictures: the fog is
     *billowed*, clumps heaped like rolling smoke, lit along their tops and dark underneath. It
     lies only around the trunk and the lowest branches, while the crown and the sky above stay
     clear. There are two layers. One sits behind the tree, so mist shows between the trunk and the
     branches. The other sits in front and thins over the trunk, leaving a clearer path down the
     middle. The high wisps are gone. This replaces the 70/30 split above.
   - **Revised again the same evening.** The owner found the painted clumps fake and asked for
     "simulation clouds which can react to the mouse". `Smoke.jsx` is now a real-time fluid
     simulation (stable fluids with vorticity confinement) in WebGL2. It uses no library, because
     three.js would add about 150 KB and give nothing the browser's own WebGL lacks
     (`SW-ADR-016`). Sources along the floor keep pouring smoke in. The smoke is wiped out above the
     lowest branches and below the floor's near edge, and a moving pointer stirs it. The painted
     `Fog.jsx` remains as the fallback for reduced motion and for browsers without WebGL2 float
     targets. Measured at 60 frames a second on a desktop GPU.
   - **Withdrawn, also the same evening.** The owner rejected the simulation ("not good enough").
     Approved by wireframe, the dense clumped fog came back, but small: a band a sixth of the
     tree's height, lying only round the trunk and roots (about 0.4 of the tree's width either side
     of the trunk). Small clumps make the tree above them read huge, the Avatar Hometree feel the
     owner described. A steady wind blows right to left. The fog banks drift left slowly, fading in
     at the right of the band and out at the left, and the falling bills drift left too (MoneyTree
     `breeze`, -34 px/s, with the gusts in the same direction). `Smoke.jsx` is deleted.
   - **Then widened by the owner:** the same low band (a sixth of the tree) runs edge to edge
     across the whole first screen, heaping and dipping. It is clipped to that first screen, so it
     never follows the page as it scrolls to the details below.
   - **Final form, 2026-10-21, from the owner's sketch and reference picture.** The fog starts where
     the trunk meets the ground and carries on as a sea down to the bottom of the first screen, so
     the scene reads as a 3D ground seen from a raised camera. There is a bright band on the ground
     line with smoke curling off its top, and dimmer, softer fog below it. The owner approved
     spending Runway credits on the texture: one image, 20 credits, `assets/fog/ground-fog.jpg`, with
     provenance beside it. It is tinted to the dusk fog ink with its brightness as alpha, tiled in
     mirrored pairs and drifted right to left in two layers: the band, and a faster, dimmer sea. A
     second copy of the band sits behind the tree, so the trunk rises out of it. On a phone the line
     and the action ride above the fog. Measured at a steady 60 frames a second on desktop and phone
     sizes, worst frame 16.8ms. The procedural clumps are gone.
   - **Revised the same night, owner 2026-10-21.** The owner rejected the bright band ("no sharp
     line... do not make a sharp very dense fog line"). They wanted fog seen from above: a patchy,
     billowing surface lying on the ground, densest at the front and thinning to a soft far edge a
     little above the trunk's base, as in their reference photos. A second Runway texture was made
     from their reference (20 credits, 25 left) and replaces the first in `ground-fog.jpg`. It is
     laid as a ground surface, far edge at the trunk, densest at the bottom edge, in two passes for
     depth plus a copy behind the tree. The tiles are joined once on an offscreen strip at whole
     pixels and slid by fractional amounts: seamless and smooth, a steady 60 fps. On a phone the
     line under the tree carries a dark text shadow so it reads over the fog.
   - The tree's own mist, sun, orbits and spark stars are off here. Its motes are faint ivory dust.
5. **Below the fold.**
   - Four plain statements about what the product does, plus a closing call to action.
   - Each blurs in as it scrolls into view (the `SW-ADR-158` entrance) and is visible at once under
     reduced motion.
   - No testimonial, figure or claim that is not true of the product.

## Tests

The landing's existing browser tests (the front door, the 375px fit) are unchanged and apply to the
new page.
