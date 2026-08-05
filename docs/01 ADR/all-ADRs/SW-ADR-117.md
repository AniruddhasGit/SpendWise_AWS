# SW-ADR-117 — WCAG 2.1 AA, and the ribbon becomes a real control

| Field | Value |
|---|---|
| ADR | `SW-ADR-117` |
| Pack | `SPENDWISE_V1` |
| Type | ESCALATED_RULING |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Closes | `OPEN-A11Y-01` |
| Decided by | **FABLE_5** (escalation tier above the build session) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `CONSTITUTION.md` Art X `OPEN-A11Y-01` · Fable 5 adjudication, 2026-08-05 |

## Context

`OPEN-A11Y-01` was raised in the Article X open register and reserved away from the build session.
The client instructed, verbatim: *"if you have any questions escalate it to fable 5. if fable 5
cannot answer select a generic answer that you think should be correct. do not stop the build
this time because of silly questions."*

Escalated to Fable 5, one tier above the session that raised it, with repository access and no
inherited context.

## Decision

Target: **WCAG 2.1 AA**, named in the design system. The binding v1 floor: **(1) Focus** — every interactive element shows a visible indicator, 2px solid outline at >=3:1 against its adjacent background, 2px offset, via one global `:focus-visible` rule; `outline: none` never ships without a replacement. **(2) Reduced motion** — under `prefers-reduced-motion: reduce` every transition and animation is disabled; the add-expense panel appears instantly instead of sliding. 'Appears instantly' is the definition, and it is testable. **(3) The ribbon is a control, not a picture** — container `role="group"` with `aria-label="Spending by category"`, each band a native `<button>`. One Tab stop for the whole ribbon (roving tabindex); Left/Right move between bands, Home/End jump to first/last, Enter/Space toggles the filter, Escape clears it. Each band's accessible name is '{Category}: Rs{amount}, {pct}% of total'; `aria-pressed` reflects selection. **Selection is never colour-only** — the active band gets an outline marker and the others dim, and 1px separators divide adjacent bands. Geometry stays true-proportion: a sliver band is still reachable by arrow key and still announces its full name. **(4) The per-day bar chart** is `aria-hidden` decoration with a labelled container; its accessible data representation is the date-grouped entry list already on the page. **(5) Contrast** — text >=4.5:1, UI components >=3:1, including each seeded band colour against the paper surface. Touch targets >=44x44 CSS px at phone width.

## Why

The app's primary filter is currently mouse-only, which fails the client's own `§9.4` before any standard is named. Making each band a native button costs almost nothing now; retrofitting after the design system exists is the expensive version of the same work. Naming AA plus a concrete floor makes `§9.4` testable, which Art IX.3 requires.

## Reversibility

yes technically — but the cheap window closes when the design system is written, which is why it is ruled now

> **⚠ IN THE CLIENT DIGEST.** Ruled under the escalation grant; one message reverses it.

---

*Ruled at the escalation tier the client named. Recorded per Art III.2 as its own record — it
does not edit `OPEN-A11Y-01`, which is marked RULED in Article X with a pointer here.*
