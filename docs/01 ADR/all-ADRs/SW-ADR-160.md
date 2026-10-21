# SW-ADR-160 — The signed-out scene: an instant front, a styled arrival, the tree carried to sign-in

| Field | Value |
|---|---|
| ADR | `SW-ADR-160` |
| Pack | `SPENDWISE_V1` |
| Type | DESIGN_SYSTEM |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | **CLIENT**, instructions 2026-10-21, approved by wireframe |
| Decision date | 2026-10-21 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Extends | `SW-ADR-016` (two client libraries: GSAP, Lenis) |
| Amends | `SW-ADR-159` (the landing's arrival; light mode for the scene) · `SW-ADR-156` (the sign-in page joins the scene) |
| Sources | owner instructions 2026-10-21 · wireframe "Flow" board · `SW-ADR-014` · `SW-ADR-020` |

## Context

On Render's free plan the server sleeps after about 15 minutes idle. A visitor then sees Render's
own "waking up" page for 30 to 60 seconds. The owner chose the free fix: an always-on front. They
also asked for the following:

- the tree and fog to appear instantly, with a countdown until the site opens;
- the rest of the landing page to pop in "smoothly with some style" when it opens;
- smooth scrolling everywhere;
- one light/dark switch on the landing and sign-in pages, dark by default, with matching colours;
- the same tree carried to the sign-in or create-account page. The tree shrinks smoothly while the
  old words leave and the new ones arrive dramatically, and the fog draws in round the tree.

The owner also ruled: **no reduced-motion fallback** on these pages. They said "do not want that
reduced motion thing".

## Decision

1. **Libraries.** `gsap` 3.15.0 (Standard no-charge licence, free for commercial use, not open
   source) and `lenis` 1.3.26 (MIT), both exact pins at least two weeks old. They are added to the
   client, not substituted, so `SW-ADR-016` is extended. Their source repositories are not copied
   into this repo: the owner's reusable skills for them live in `D:\Project\claude_leash`.
2. **The instant front.**
   - The page shows the tree and fog at once. `lib/scene.js` asks `/healthz` every 2.5s while a
     visitor waits. That endpoint touches no database, so Neon is not polled, and it stops once
     the server answers, so it is not a keep-awake ping.
   - The countdown starts at 45s and appears only after 350ms, so a server that is already awake
     never flashes it. It opens the moment the server answers, and past zero it reads "Almost
     there" rather than going negative.
   - The session check (`/api/auth/me`) waits for the server.
3. **The arrival.** A GSAP timeline, about 1.5s: the bar slides down, the headline is split into
   letters that rise through a 3D turn, the line sharpens up, the button springs in, then the
   scroll cue. Below the fold, ScrollTrigger lifts and sharpens each detail as it is scrolled to.
   This replaces the `.sw-focus` blur-in on the landing.
4. **Smooth scroll everywhere.** Lenis runs on GSAP's ticker, one loop shared with ScrollTrigger.
   The expense panel and the side rail scroll natively (`data-lenis-prevent`).
5. **One scene, one switch.**
   - The landing and sign-in pages share the scene and a sun/moon switch.
   - The scene is **dark unless light was chosen**, so "System", the app's default, shows dark
     there.
   - While signed out, the whole document wears the scene's theme, so the card and inputs match.
     Signing in restores the person's own choice.
   - Light mode is the same scene at dawn: new `--sw-dawn-*` tokens, which the dusk tokens are
     pointed at.
6. **Carrying the tree.**
   - The words leave first: the headline's letters scatter, the side text slides off, the bar
     lifts away.
   - The browser's own View Transitions then morph the tree picture (`sw-tree`) from the landing
     to its sign-in spot in 950ms. The glass floor fades as the tree leaves it.
   - The landing fog sinks and dissolves while the sign-in page's fog gathers in round the tree.
     The fog is a pool there (`<Fog pool>`).
   - The sign-in words then arrive one after another. "Back to the home page" plays the same move
     in reverse.
7. **Motion preference.** On the signed-out scene the tree, the fog and these animations run
   whatever the visitor's `prefers-reduced-motion` setting, by the owner's ruling. The signed-in
   app keeps its existing reduced-motion behaviour.
8. **Hosting.** The front is a Render free static site serving the same `client/dist`. Rewrites
   send `/api/*` and `/healthz` to the web service, so the browser stays same-origin (no CORS,
   `SW-ADR-020`), and it carries the API's security headers. **Created 2026-10-21 with the owner's
   permission:** `spendwise-front`, service `srv-dbbu5rg473hc73cias3g`,
   https://spendwise-front.onrender.com. Verified through it: the page and its security headers,
   `/healthz` (200, empty), a GET to `/api/auth/me` (401 JSON), and a POST to `/api/auth/login`
   (401 JSON, shown as "Wrong email or password" in a real browser). A real sign-in carrying the
   session cookie through the rewrite was not tested by the build session (no test credentials),
   so it is **unverified until the owner signs in there**. It does not auto-deploy: deploy it
   alongside the web service.

9. **Into the dashboard and back** (owner, later on 2026-10-21).
   - A successful sign-in or new account lifts the sign-in words away. The same tree then glides
     from the sign-in page to its place on the dashboard, and the sign-in fog dissolves.
   - The morph waits, frozen on the old page, until the dashboard has drawn its tree, at most
     2.5s. After that the tree fades across instead.
   - A new account's first screen now shows the tree, with no falling bills (`drops={false}`).
     Example spends on an empty personal ledger could be mistaken for real ones.
   - Signing out carries the tree back to the sign-in page.
   - While a tree is being carried, its page's own CSS entrance is off. Otherwise the browser
     captures it invisible, mid-entrance. It stays off for that screen (`.sw-carried`), because
     lifting the override would replay the entrance.

10. **The dashboard's fog, and the scene's colours** (owner, later on 2026-10-21).
    - The dashboard's tree, and the tree on a new account's first screen, stand in the same fog
      pool as on the sign-in page, and the sign-in fog glides into it as you land. The fog
      follows the app's theme: the dawn ink on a light page.
    - On a phone the pool stays within the tree's width, because nothing may reach past a 375px
      screen.
    - "More ivory and reddish, way too much olive": the scene is now an ember dusk. The dusk
      tokens are warm near-black and umber, the fog and type are the brand ivory, and the
      actions are vermilion. The headline's 3D shadow is vermilion too, and links stay ivory with
      a vermilion underline.
    - Light mode is warm brown ink on the brand ivory, with a taupe fog.
    - The sign-in card and inputs use the scene's warm inks. The tree stays the one green.
    - Measured contrast:
      - ivory on the vermilion button 5.33:1;
      - quiet ink on umber 7.90:1;
      - dawn quiet ink on ivory 6.71:1;
      - every other pair above 13:1.

11. **The owner's colour rule for the whole site** (2026-10-21), superseding the "ember dusk" of item 10.
    - **Emerald is primary, warm ivory secondary, vermilion the third colour.** Light mode swaps
      emerald and ivory.
    - The signed-out scene now uses the app's own emerald-and-ivory family, so the landing, the
      sign-in page and the dashboard share one palette. Dark mode is a deep emerald night with
      ivory type and fog. Light mode is ivory ground with emerald ink and a soft emerald-grey fog.
    - Buttons are the app's emerald.
    - Vermilion is used the way the poster uses it, more than a hint:
      - the landing's right-hand line as a block of vermilion display type;
      - the orbit lines and spark stars around the tree, now on;
      - the detail numbers and the closing line;
      - the sign-in card title and lede;
      - the outlined quiet buttons and the link underlines;
      - the headline's 3D depth;
      - the dashboard's card headings, alongside its existing vermilion total label, orbit and
        projection.
    - Vermilion text uses `--sw-gold` (vermilion per theme): 5.33:1 on ivory and 6.9:1 or more on
      the emerald. Lines and stars use the brand `#E34222`.
    - **No halo:** the tree's glow (`.mt-stage::before`) and the dashboard's frosted disc behind
      the tree are gone.
    - The fog pools fade with a long bell-shaped falloff and never show an edge. On the dashboard
      the pool may drift over neighbouring cards, by the owner's ruling. It never takes clicks.

12. **The wake check, corrected** (2026-10-21, a bug the owner hit in Brave). Item 2's poll of
    `/healthz` was blocked by ad-blockers (`ERR_BLOCKED_BY_CLIENT`), which left the visitor waiting
    for ever.
    - The check now asks `/api/auth/me`, the call the app makes first anyway. Any JSON answer means
      the server is up, and HTML means the host's waking page. With no session cookie the 401 needs
      no database.
    - After three fast network-level failures in a row the site opens anyway (bug ledger).

## Consequences

- The front lives at a new `*.onrender.com` address. The old address keeps working, but a visit
  to it while the server sleeps still shows Render's page.
- The owner's motion ruling means people who ask their device for reduced motion get the full
  animation on these two pages. It is recorded so it can be reversed with one instruction.
- Browsers without View Transitions (older Firefox) switch pages instantly, with the entrances
  still played.

## Tests

The browser suite passed in full, 57/57, after the change. On the first run two tests failed
intermittently; both passed when run alone and in a second full run. Flow screenshots were checked
for: the countdown under a simulated sleeping server, the arrival, the carry-over both ways, light
mode, a 390px phone (no overflow), and a steady 60 fps on the landing.
