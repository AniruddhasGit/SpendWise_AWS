# SW-ADR-090 — Whether the `users` table may sit outside row-level security

| Field | Value |
|---|---|
| ADR | `SW-ADR-090` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | AUTHORITY_RETURNED_TO_CLIENT |
| Supersedes | `SW-ADR-042` |
| Raised by | QA FINDING-7 (HIGH) — authority |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-042` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-042` removed RLS from `users` and said so in its own text: "the one table holding every email and password hash is outside the database-layer guarantee. That is a real reduction in the `SW-ADR-018` promise." Art IX.6 reserves **waiving a quality check** to the client — and states the test explicitly: adopting the *stricter* option is not a waiver, which is exactly why `SW-ADR-018` itself could be ruled by the build session. `SW-ADR-042` fails that test in the opposite direction.

## Decision

**The ruling is **withdrawn**. The question returns to the client as `OPEN-USERSRLS-01`, with two real options rather than one recommendation.**

## Consequences

- The technical reasoning stands and is not in dispute: a GUC-keyed policy genuinely cannot serve a pre-authentication lookup, and `SRC-001 §10.5`'s timing defence genuinely needs that lookup to return empty rather than error.
- The stricter alternative the original ADR never offered — a separate pre-auth role holding `SELECT`/`INSERT` on `users` and `password_resets` only — is now on the register so the client is choosing between two options, not ratifying one.
- `SW-ADR-071` shows the same root cause reached `password_resets`. Both tables are covered by the one open row, because they are one decision.

---

*This record does not decide the question. It withdraws a decision the build session was not
entitled to make and returns it to the client. Art III.2: reversal happens by a new record,
never by editing the old one.*
