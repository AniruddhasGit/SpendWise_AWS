# Self-hosted faces

## Current: Geist, one file (2026-10-18, liquid-glass revision)

| File | Family | Role | Licence | Source |
|---|---|---|---|---|
| `Geist-Variable.woff2` | Geist, variable `wght` 100–900 | every `--sw-font-*` token | SIL OFL 1.1 (`OFL-geist.txt`) | official release `vercel/geist-font` **v1.8.1**, `geist-font/Geist/webfonts/Geist[wght].woff2`, unmodified, renamed only |

sha256 `9ce2d97863cab59a0c7522534112d6c42a4e25c0e6b2ab37766761b0f82cfbd6`.

**One file, no subset split.** The release's `Geist[wght].ttf` was read with a cmap/GSUB reader:
U+20B9 (₹) is present, and so is `tnum`. In a browser, `document.fonts.check('16px Geist', '₹')`
returned `true` and the face reported `loaded`. Declared in `src/styles/glass.css`, preloaded in
`index.html`. The OFL requires the licence to travel with the font, so `OFL-geist.txt` must not be
pruned.

## Legacy (no longer referenced by any token)

The six Bricolage Grotesque / DM Sans / JetBrains Mono files below are still declared by
`app.redesign.css`. A browser only fetches a face that some element uses, and nothing does any more,
so they are not downloaded. They go with the legacy-CSS cleanup.


Three families, six files. Added 2026-08-21 by `CR-002` / `SW-ADR-152`.

`SW-ADR-020` rejected a CDN for the frontend on single-origin grounds, and the same reasoning
applies to fonts — a `fonts.gstatic.com` request is a third party learning every page load.

**Before this directory existed there was no `@font-face` rule anywhere under `client/`.** The
three families were named in `tokens.css` and never loaded, so the application rendered OS
fallbacks for its entire life, including in every screenshot under `evidence/` dated before
2026-08-21.

## Why two files per family

`U+20B9` — the rupee sign — is in the **`latin-ext`** subset, not `latin`. `latin` carries
`U+20AC`, the euro. Shipping the `latin` file alone renders every `₹` in this product from a
fallback font while the digits beside it come from JetBrains Mono, in an application whose entire
subject is columns of money.

The `unicode-range` values in `app.redesign.css` are Google's own, read off the source stylesheet
rather than retyped.

## Provenance and licence

| Family | Role | Licence |
|---|---|---|
| Bricolage Grotesque | `--sw-font-display` | SIL Open Font License 1.1 |
| DM Sans | `--sw-font-body` | SIL Open Font License 1.1 |
| JetBrains Mono | `--sw-font-mono` | SIL Open Font License 1.1 |

Fetched from the Google Fonts CSS2 API as variable woff2, one file per family per subset. Each
family's full licence text sits beside it as `OFL-<family>.txt` — **the OFL requires the licence to
be distributed with the font**, so those files are not optional and must not be pruned as clutter.

None of the three is modified. No Reserved Font Name is used in any derivative, because there is no
derivative.
