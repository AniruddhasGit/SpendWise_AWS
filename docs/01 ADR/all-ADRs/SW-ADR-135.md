# SW-ADR-135 — Read-audits: the audit row is the change, and disclosure waits for its COMMIT

| Field | Value |
|---|---|
| ADR | `SW-ADR-135` |
| Pack | `SPENDWISE_V1` |
| Type | TECHNICAL |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 exit gate — transaction semantics of the three read-audit types |
| Decided by | **FABLE_5** (escalation tier, under the client's standing instruction) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §10.8` · `SW-ADR-105` · `SW-ADR-083` · Art VI.2 · Fable 5 adjudication, 2026-08-05 |

## Context

`SRC-001 §10.8`: *"Every admin action writes to the audit log in the same transaction as the
change. If the log write fails, the change rolls back."* `SW-ADR-105` created three **read**-audit
types — `users_list_viewed`, `sessions_list_viewed`, `audit_log_viewed`. A read has no change to
be in the same transaction as, so the rule appeared not to compose with itself.

*(The same-transaction rule is Art **VI.2**. An earlier draft of this question cited Art IV.8,
which is the no-f-strings-near-SQL rule.)*

## Decision

**The audit row is the change; the read is the disclosure it records.**

`§10.8` is a conditional atomicity rule — when an admin action has an effect, the effect and its
record commit or fail as one — not a prohibition on audit rows absent a data change. The reading
that forbids read-audits would put `§10.8` in conflict with `SW-ADR-105`, and Art II.1 obliges the
reading under which both APPROVED records compose.

For a read, the effect **is** the disclosure, and the only database change is the audit row
itself. The rule transposes exactly: **data leaves the server only if the read-audit row commits.**

```
BEGIN
  INSERT the read-audit row
  SELECT the data
COMMIT
  → only now serialise the response
```

Any failure of the `INSERT` or the `COMMIT` yields a 5xx **with no data returned**. That
withholding *is* the read's rollback — the precise contrapositive of `§10.8`.

## Consequences

- **An audited admin GET can never be served from a read-only path.** Not a read-only transaction
  (the `INSERT` fails), not a replica (cross-node atomicity does not exist), not a cache (a hit
  would disclose without its one-row-per-request record). `/api/admin/users`,
  `/api/admin/sessions` and `/api/admin/audit` run **read-write on the primary**, one transaction
  per request.
- One row **per request**, including each repeated pagination page. An empty result still audits —
  the admin looked.
- **A 403 to a non-admin writes nothing to the audit ledger.** The allowlist is closed and has no
  denied-attempt type; refused attempts belong to the request log (`P-OPS-05`) and `SW-ADR-104`.
- Append-only is untouched: `INSERT` is the one verb the immutable table permits (`SW-ADR-083`).
- HTTP `GET` safety is not offended — RFC 9110 expressly permits server-side logging as a side
  effect of a safe method.
- This is the **strictest** available reading, so under Art IX.6 it needed no signature.
- Recorded in `GOTCHAS.md` so a future "optimise the admin reads onto a read-only path" session
  trips over the trap ledger rather than over `SW-ADR-105`.

---

*Ruled at the Fable 5 escalation tier.*
