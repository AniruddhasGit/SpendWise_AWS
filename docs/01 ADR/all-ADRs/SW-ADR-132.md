# SW-ADR-132 — Correcting the supersession graph: a labelling record is not a superseding one

| Field | Value |
|---|---|
| ADR | `SW-ADR-132` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — (it repairs links, it does not replace a decision) |
| Raised by | GOAL_13 exit gate — a topic-coherence audit of all 22 supersessions |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-023` · `SW-ADR-030` · `SW-ADR-041` · `SW-ADR-077` · `SW-ADR-088` |

## Context

Every superseding link in this pack was checked for **topic coherence**: does the successor
actually cover the subject of the record it replaces? Twenty-two links, three broken. All three
were invisible to the consistency checker, because a link that *resolves* is not a link that is
*true* — the same failure shape as the citation drift of `SW-ADR-092`'s pass, one level up.

**1. `SW-ADR-088` supersedes nothing, and marking it a supersession withdrew a live decision.**
`SW-ADR-088` is a *labelling* record: it declares that every AWS-touching claim in `SW-ADR-023`,
`047`, `065`, `068`, `069` and `070` is `UNVERIFIED — reasoned, not observed`. It names six
records in its Decision and put the **first of them** in its `Supersedes` field. The banner
machinery then marked `SW-ADR-023` SUPERSEDED and the ledger followed.

`SW-ADR-023`'s decision is **"BIGINT identity on every table."** Every primary key in
`datamodel.json`, every `id` column in `schema.sql`, and the 404-not-403 argument in `P-PRV-03`
rest on it. **It was silently withdrawn by a bookkeeping side effect**, and then cited fourteen
times as live authority — which was, accidentally, the correct reading.

The GOAL_13 repair pass made it worse before it made it better: it re-pointed all fourteen
citations to `SW-ADR-088`, a record about AWS-claim labelling that says nothing about primary
keys. That re-pointing is reverted here and the error is recorded rather than quietly undone.

**2. `SW-ADR-077` replaced only part of `SW-ADR-030`, and the rest fell on the floor.**
`SW-ADR-030` decided two things: the module→table **ownership map**, and that every admin read is
a service call. `SW-ADR-077` replaced the second — its Context says so — and superseded the whole
record. The ownership map went with it. `SW-ADR-129` then superseded `SW-ADR-077`, orphaning it
twice, which is why the PRD read "Ownership map in `SW-ADR-077`" for a record that never had one.

**3. Two records claim to supersede `SW-ADR-041`, and the banner names the wrong one.**
`SW-ADR-071` (password resets leave RLS) and `SW-ADR-078` (correcting `SW-ADR-041`'s premise
about RLS write behaviour) both carry `Supersedes: SW-ADR-041`. The banner on `SW-ADR-041` names
`SW-ADR-071` — the incidental one. The record that actually corrects its premise is `SW-ADR-078`.

## Decision

**A. `SW-ADR-023` returns to `APPROVED`.** It was never superseded. Its AWS-touching claim carries
`SW-ADR-088`'s `UNVERIFIED — reasoned, not observed` label; its primary-key decision is live and
is the authority every `id` column cites.

**B. `SW-ADR-088`'s `Supersedes` field is cleared.** A labelling record amends the records it
names; it replaces none of them. Its type is `ANNOTATION`.

**C. The module→table ownership map is restated here as live authority**, unchanged from
`SW-ADR-030`:

| Module | Owns |
|---|---|
| `auth` | `sessions`, `password_resets` |
| `users` | `users` |
| `expenses` | `expenses` |
| `categories` | `categories` |
| `admin` | `admin_audit_log` |
| `receipts` | **no table** — it operates on `expenses.receipt_key` through the expenses service |

`app_meta` is owned by `core`, which `SW-ADR-125` added after `SW-ADR-030` was written and which
no record had assigned.

**D. `SW-ADR-041`'s primary successor is `SW-ADR-078`.** `SW-ADR-071` amends it on a second,
narrower point. The banner names both, in that order.

## Consequences

- **A supersession is a claim, and claims get checked.** `tools/consistency_check.py` gains a
  topic-coherence assertion over the supersession graph, in the same review channel as
  `citation-topic` — it is a heuristic and must not gate, but it is the heuristic that found
  all three of these.
- **A record that names several ADRs in its Decision must not put one of them in `Supersedes`.**
  That field means "this replaces that". `SW-ADR-088` meant "this annotates those".
- The GOAL_13 repair pass propagated defect 1 across fourteen citations before catching it. That
  is recorded in `12 DesignReview` rather than erased: a repair pass that trusts upstream metadata
  inherits upstream defects, and this one did.
- Nothing about the *behaviour* of the system changes. All three defects were in the map, not the
  territory — which is precisely why nothing downstream noticed.

---

*This record repairs links. It replaces no decision, so it supersedes nothing.*
