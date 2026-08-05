# Error code registry — GENERATED from contract.json. DO NOT HAND-EDIT.

`SW-ADR-051` states in its own Consequences that *"a stable `code` is the only thing
that lets the PRD write a binary acceptance criterion for an error path, which the
Definition of Done requires."* The registry that makes that true was never written, so
`CONSTITUTION.md` Art IX.3 could not be met on any error path. `SW-ADR-138` writes it.

**Envelope.** `{"error": {"code": "...", "message": "...", "field": "..."}}`

`field` carries the CLIENT's name for the input - `amount`, never `amount_paise`.

| `code` | Status | Carries `field` | When |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | yes | any input fails a stated rule |
| `NOT_FOUND` | 404 | no | not-yours or not-found, on every verb (P-PRV-03) |
| `UNAUTHENTICATED` | 401 | no | no credential presented |
| `SESSION_INVALID` | 401 | no | credential presented but revoked, expired, idle-timed-out, signed with a rotated secret, or **otherwise unverifiable** — a bad signature, alg=none, a missing claim or a structurally broken token. UNAUTHENTICATED is only for no credential at all, so a tampered token has exactly one code that fits. |
| `ACCOUNT_DEACTIVATED` | 401 | no | valid session, is_active false |
| `FORBIDDEN` | 403 | no | authenticated but the role does not hold the capability |
| `EMAIL_TAKEN` | 409 | yes | registration against an existing address, subject to SW-ADR-102's enumeration posture |
| `CONFLICT` | 409 | yes | duplicate category name; last-administrator guard |
| `RATE_LIMITED` | 429 | no | a rate limit is hit; carries Retry-After |
| `BAD_REQUEST` | 400 | no | malformed body that never reaches validation |
| `INTERNAL` | 500 | no | unhandled; the message is generic and never carries detail |

**A code not on this list cannot be returned.** The list is closed, in the same way
the audit-log action allowlist is closed (`SW-ADR-105`): an unlisted value is a defect,
not an extension point.

## Messages — one per rule

One message per rule. The `field` column names which input a pairwise rule reports. `field.required` and `field.type` were missing until 2026-08-05: the registry was written with the argument that '422 naming the cap' is a binary assertion on a string nothing specified, and that argument was applied to eleven value rules and then stopped - while absence and type are more common in real traffic than every value rule combined.

| Rule | `field` | Message |
|---|---|---|
| `field.required` | `<the missing key>` | {field} is required. |
| `field.type` | `<the ill-typed key>` | {field} must be {expected}, for example {example}. |
| `amount.scale` | `amount` | Amount must have at most two decimal places. |
| `amount.grammar` | `amount` | Amount must be a decimal string, for example "1250.00". |
| `amount.bounds` | `amount` | Amount must be greater than zero and at most 10000000000.00. |
| `spent_on.window` | `spent_on` | Date must be within the last 10 years and no more than 1 year ahead. |
| `description.length` | `description` | Description must be at most 500 characters. |
| `category.not_owned` | `category_id` | That category does not exist. |
| `range.order` | `to` | The end date must not be before the start date. |
| `range.span` | `to` | A range may span at most 400 days. |
| `range.floor` | `from` | The start date must be on or after 2000-01-01. |
| `range.required` | `from` | Both from and to are required; there is no default range. |
| `filter.exclusive` | `uncategorised` | category_id and uncategorised cannot both be given. |

**Placeholders.** `{field}`, `{expected}` and `{example}` are substituted at render time. The rendered sentence is what a test asserts on, so the substitutions are part of the contract.

| `{field}` | `{expected}` | `{example}` |
|---|---|---|
| `amount` | a decimal string | `"1250.00"` |
| `spent_on` | a date | `"2026-08-01"` |
| `category_id` | an integer or null | `3` |
| `description` | a string or null | `"Auto to office"` |
| `from` | a date | `"2026-08-01"` |
| `to` | a date | `"2026-08-31"` |

## Precedence — when one body breaks two rules

**Report the FIRST failure in the order below and stop. Validation short-circuits; it does not collect.**

The envelope carries exactly ONE field and ONE message, and every negative case varies exactly one input - so nothing forced this question and nothing answered it. Two engineers would have implemented opposite orders and both passed their own tests, which is the Art IX.3 failure: an acceptance criterion with a 50/50 expected value is not binary.

Presence before type before value, then fields in the order §6.1's worked payload lists them. `category.not_owned` is last because it is raised by the database, after every in-process rule has already passed.

```
field.required -> field.type -> amount.grammar -> amount.scale -> amount.bounds -> spent_on.window -> description.length -> range.required -> range.order -> range.span -> range.floor -> filter.exclusive -> category.not_owned
```
