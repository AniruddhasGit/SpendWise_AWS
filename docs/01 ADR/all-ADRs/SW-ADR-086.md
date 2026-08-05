# SW-ADR-086 — Seed idempotency without a delete path

| Field | Value |
|---|---|
| ADR | `SW-ADR-086` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | `SW-ADR-067` |
| Raised by | QA FINDING-23 (LOW) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-067` · the GOAL_02 adversarial review, 2026-08-05 |

## Context

`SW-ADR-067` said the seed script is idempotent because it "deletes and recreates its own two users" — while confining itself to the real registration and expense endpoints. **There is no delete-user endpoint**, and `OPEN-USERDEL-01` (IRREVERSIBLE) recommends there never be one in v1. The only route left was the direct SQL the ADR rejected.

## Decision

**Idempotency comes from `SW-ADR-068`'s `spendwise_test` database being dropped and re-migrated wholesale between runs — which the `SW-ADR-009` evidence ladder already requires. The script itself is additive: fixed namespaced emails, skip creation if present.**

## Consequences

- No user-deletion capability is acquired by the back door.
- The seed script must refuse to run against any database whose name is not `spendwise_test`. A seeder that can point at `spendwise_dev` is a data-loss incident waiting for a typo.

---

*A superseding record, not an edit. `SW-ADR-067` keeps its original text with a banner pointing here —
Art III.2: accepted decisions are immutable, reversal happens by a new record.*
