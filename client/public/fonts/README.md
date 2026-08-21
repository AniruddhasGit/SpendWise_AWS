# Self-hosted faces

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
