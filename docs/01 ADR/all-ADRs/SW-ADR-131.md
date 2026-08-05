# SW-ADR-131 — The Uncategorised bucket is `#948c87`

| Field | Value |
|---|---|
| ADR | `SW-ADR-131` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-113` (in full — every ruling restated below) |
| Raised by | GOAL_13 uncoached slice GUESS #12 · X-01 FINDING-7 |
| Decided by | BUILD_SESSION (under `SW-ADR-015` and Art IX.6) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-113` · `SW-ADR-092` · `SW-ADR-117` |

## Context

`SW-ADR-113` specified the synthetic Uncategorised bucket as `#a8a29e`. Measured against paper
that is **2.36:1** — below the **3:1** floor `SW-ADR-117` sets for a UI component under
WCAG 2.1 AA. The design system darkened it within the same hue to `#948c87`, **3.09:1**, and the
PRD, the design tokens and both journeys followed.

It cited `SW-ADR-092`'s licence — *"the design system adopts these as tokens and MUST verify each
at >= 3:1, adjusting tone within hue if any fails"*. But `SW-ADR-092` governs **the eight seeded
categories**, and Uncategorised is not one of them. The change was right and the authority for it
was missing, so `SW-ADR-113` still read as live authority for a value nothing implements.

*(Both contrast figures were independently recomputed during the GOAL_13 exit gate and match to
two decimal places.)*

## Decision

**The Uncategorised bucket is `#948c87`.** `SW-ADR-092`'s verify-and-adjust licence extends
explicitly to every colour the design system renders, including synthetic buckets that are not
rows in `categories`.

**`SW-ADR-113`'s other rulings are restated here unchanged, so exactly one live record carries
the whole bucket** — a partial supersession would need a status this pack's vocabulary does not
have, and inventing one is how `SW-ADR-023` got withdrawn by accident (`SW-ADR-132`):

- id `null` — it is a synthetic bucket, not a row in `categories`; nothing joins to it
- label `Uncategorised`
- **always ordered last, regardless of size**

## Consequences

- Nothing downstream changes — the PRD, `tokens.css`, the design system and both journeys already
  say `#948c87`. This record makes them *right* rather than merely consistent.
- Adopting a **stricter** option is not a waiver (Art IX.6), so this needed no client signature.
  What it did need was a record, and for a session that was the whole lesson: the measurement was
  published, the value was changed, and the authority was left dangling for one document to
  contradict another.
- A contrast floor is now a **verify-and-adjust** instruction wherever a colour is specified, not
  a value to be copied. Any future ADR naming a hex inherits it.

---

*A superseding record, not an edit. `SW-ADR-113` keeps its text with a banner pointing here —
Art III.2.*
