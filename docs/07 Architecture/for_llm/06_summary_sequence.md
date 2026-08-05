# The dashboard's single round trip

```mermaid
sequenceDiagram
    participant B as Browser
    participant R as expenses.router
    participant S as expenses.service
    participant ER as expenses.repository
    participant CS as categories.service
    participant D as PostgreSQL

    B->>R: GET /api/expenses/summary?from&to&category
    R->>S: summarise(range, category)
    S->>ER: totals + per-day + per-category-id
    ER->>D: aggregate queries (RLS scoped)
    D-->>ER: rows
    ER-->>S: ids and totals only
    S->>CS: names_for(category_ids)
    Note over S,CS: the ONE sanctioned crossing.<br/>A join would break §3.4's module rule.
    CS-->>S: id -> (name, colour)
    S->>S: stitch · append Uncategorised LAST · compute average
    S-->>B: one response
```

**The average**, computed once, server-side:

```
elapsed = max(0, min(to, today) - from + 1)     # today in Asia/Kolkata
average = round_half_up(total_paise / elapsed)
average = null when elapsed = 0                  # rendered "—", never 0
```

**Invariant, asserted in tests:** the breakdown sums **exactly** to the headline total. Null-category
rows are guaranteed to exist — deleting a category nulls the link on every historical expense — so
if the stitch dropped them, the split would sum to less than the total printed above it.

**Why the browser never recomputes this:** it would be a second implementation of the one rule the
day-one gate checks, and a drift between the two is invisible to that gate (`SW-ADR-058`).
