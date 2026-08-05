# SW-ADR-078 — Correcting `SW-ADR-041`'s premise about RLS write behaviour

| Field | Value |
|---|---|
| ADR | `SW-ADR-078` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-041` |
| Raised by | QA FINDING-4 (HIGH) — premise, not decision |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-041` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-041`'s decision is right and stands. Its stated **justification is factually wrong** and would mis-teach any session reasoning from it. It claimed a `FOR ALL … USING` policy without `WITH CHECK` lets user B write to user A's rows, and that a `FOR SELECT`-only policy leaks silently. Neither is true: PostgreSQL uses the `USING` expression as the `WITH CHECK` expression when the latter is absent, and RLS is default-deny, so a `FOR SELECT`-only policy denies **all** writes — loudly, to everyone, including the row's owner.

## Decision

**The decision is unchanged: `FOR ALL` with explicit `USING` **and** `WITH CHECK`, and the day-one proof extended to a denied write and a denied delete. The reasoning is restated: the real hazards are (i) a `FOR SELECT`-only policy causing a total write outage, and (ii) a `WITH CHECK` deliberately weaker than its `USING`.**

## Consequences

- Recorded as a superseding record rather than an edit, per Art III.2 — the wrong premise stays visible in `SW-ADR-041` with a banner pointing here.
- This is the second premise in one authoring pass that was asserted rather than verified. `GOAL_13`'s X-04 lane exists for exactly this.

---

*A superseding record, not an edit. `SW-ADR-041` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
