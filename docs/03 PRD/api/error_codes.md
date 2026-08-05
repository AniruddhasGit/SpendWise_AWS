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
| `field.required` | `<the missing or null body key>` | {field} is required. |
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
| `range.required` | `<from or to, whichever is missing; `from` when BOTH are absent>` | Both from and to are required; there is no default range. |
| `filter.exclusive` | `uncategorised` | category_id and uncategorised cannot both be given. |
| `offset.bounds` | `offset` | offset must be zero or greater. |

### One message per non-validation code

`messages.rules` covers the VALIDATION_ERROR rules only. Every other code still returns a message, and until 2026-08-05 five of them had none - while ACCOUNT_DEACTIVATED's exact sentence was specified (SW-ADR-100) and P-ACC-07's four reset outcomes were specified word for word, which is what makes the omission conspicuous rather than deliberate.

| `code` | Message | |
|---|---|---|
| `UNAUTHENTICATED` | Sign in to continue. |  |
| `SESSION_INVALID` | Your session has ended. Please sign in again. | One sentence for every cause - expiry, revocation, idle timeout, rotated secret, bad signature. Distinguishing them would tell an attacker which one they hit. |
| `ACCOUNT_DEACTIVATED` | Your account has been deactivated. Contact your administrator. | Already specified by SW-ADR-100; restated here so the table is complete. |
| `NOT_FOUND` | Not found. | Deliberately identical for not-yours and not-found (P-PRV-03). Any difference is an enumeration oracle. |
| `FORBIDDEN` | You do not have permission to do that. |  |
| `CONFLICT` | That already exists. |  |
| `EMAIL_TAKEN` | That email address cannot be used. | Wording subject to SW-ADR-102's enumeration posture. |
| `RATE_LIMITED` | Too many requests. Try again shortly. | Carries Retry-After. |
| `BAD_REQUEST` | The request body could not be read. |  |
| `INTERNAL` | Something went wrong. | Generic by rule - it never carries detail, an id, or a stack. |


**Placeholders.** `{field}`, `{expected}` and `{example}` are substituted at render time. The rendered sentence is what a test asserts on, so the substitutions are part of the contract.

| `{field}` | `{expected}` | `{example}` |
|---|---|---|
| `spent_on` | a date | `"2026-08-01"` |
| `category_id` | an integer or null | `3` |
| `description` | a string or null | `"Auto to office"` |
| `from` | a date | `"2026-08-01"` |
| `to` | a date | `"2026-08-31"` |
| `uncategorised` | true or false | `true` |
| `limit` | an integer | `50` |
| `offset` | an integer | `0` |
| `email` | an email address | `"you@example.com"` |
| `password` | a string of 12 to 72 characters | `"correct-horse-battery-staple"` |
| `display_name` | a name of 1 to 100 characters | `"Person A"` |

## Precedence — when one body breaks two rules

**Report the FIRST failure in the order below and stop. Validation short-circuits; it does not collect.**

The envelope carries exactly ONE field and ONE message, and every negative case varies exactly one input - so nothing forced this question and nothing answered it. Two engineers would have implemented opposite orders and both passed their own tests, which is the Art IX.3 failure: an acceptance criterion with a 50/50 expected value is not binary.

Presence before type before value, then fields in the order the request model declares them (see `tie_break`). `category.not_owned` is last because the database raises it, after every in-process rule has already passed.

```
field.required -> field.type -> amount.grammar -> amount.scale -> amount.bounds -> spent_on.window -> description.length -> range.required -> range.order -> range.span -> range.floor -> offset.bounds -> filter.exclusive -> category.not_owned
```

### Scope — which rule owns an absence

| Rule | Owns |
|---|---|
| `field.required` | BODY keys only. A required key that is absent OR sent as explicit `null` is `field.required`, never `field.type` - presence is checked before type, and a null in a required slot is an absence of a value, not a wrong type (G3). |
| `range.required` | The summary's QUERY pair only. A missing `from` or `to` is `range.required`, with `field` set to the key that is actually missing - not `field.required`, which would otherwise make `range.required` unreachable (G2). |

Both rules were live and `field.required` was first in the order, which read literally made `range.required` dead text. A rule that can never fire is the same defect as a missing one, and CV-07 exists precisely to describe the query-pair case.

### Tie-break — two keys, one rule class

**When two keys fail the SAME rule class, report the one that comes first in `request_models.<Model>.fields` - the declaration order, which is what Pydantic reports in. An earlier `why` cell said '§6.1's worked payload order' (amount, category_id, description, spent_on) while ExpenseCreate declares (amount, spent_on, category_id, description), so the natural implementation silently produced the other answer. The model is authoritative because it is the thing the code is built from. Found by the sixth uncoached slice, C5.**
