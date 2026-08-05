# SW-ADR-030 — Table ownership map — which module declares each model

> **⚠ AMENDED 2026-08-05 by `SW-ADR-077` (QA FINDING-11 (HIGH)).**
> The text below is retained unedited. Where it conflicts with the superseding
> record, the superseding record governs (Art III.2).

| Field | Value |
|---|---|
| ADR | `SW-ADR-030` |
| Pack | `SPENDWISE_V1` |
| Type | ARCHITECTURE |
| Decision status | **SUPERSEDED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 §3.4` · `SRC-001 §3.1` · `SW-ADR-017` |

## Context

SRC-001 §3.4 forbids a module touching another module's tables but never says which module owns which of the seven.

## Options considered

- A. Publish an explicit ownership map.
- B. Leave it to whoever writes the first model.

## Decision

**A. auth owns sessions and password_resets. users owns users. expenses owns expenses. categories owns categories. admin owns admin_audit_log. receipts owns no table — it operates on expenses.receipt_key through the expenses service.**

## Consequences

- receipts owning no table is the notable one: it means SRC-001 §7.5's four endpoints route through the expenses service rather than writing the column directly, which keeps §3.4 intact.
- admin owns only the audit log; every other admin read is a service call, per SRC-001 §3.4's own worked example.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
