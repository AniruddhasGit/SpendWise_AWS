# SW-ADR-025 — Asia/Kolkata is the application calendar

> **⚠ NOT CURRENT AUTHORITY.** The ledger records this record as `RETIRED`. The text
> below is history — for status trust the ledger (Art XI.1).

> **⚠ WITHDRAWN 2026-08-05 by `SW-ADR-089`.** This ruling exceeded the build session's
> authority — it is IRREVERSIBLE by its own text. The question is now `OPEN-TZ-01`, for the
> client. The analysis below stands; the decision does not.

| Field | Value |
|---|---|
| ADR | `SW-ADR-025` |
| Pack | `SPENDWISE_V1` |
| Type | PRODUCT_RULE |
| Decision status | **RETIRED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-010` · `SW-ADR-013` · `SRC-001 §7.4` |

## Context

SW-ADR-010 caps the daily-average denominator 'at today', which the SERVER must evaluate. No timezone is named anywhere. On a UTC server, an IST user's first 5.5 hours of every day still count as yesterday: between 00:00 and 05:29 IST the denominator is one day short and the average jumps 20-25%. On the 1st of a month in that window the denominator can reach zero.

## Options considered

- A. One fixed application timezone in config: Asia/Kolkata.
- B. The client sends its own 'today' per request.
- C. Per-user timezone column.

## Decision

**A. Asia/Kolkata, named in settings. The server computes 'today' in it. `spent_on` is never defaulted server-side — the browser sends it explicitly.**

## Consequences

- SW-ADR-013 already fixed the product at INR, so a single Indian calendar is consistent with scope rather than a new assumption.
- B was rejected because a client-supplied value would then determine a displayed money figure and the day-one gate's expected 75810 would depend on the caller.
- This is IRREVERSIBLE on the write path: the submission instant is not stored, so rows misfiled across a day boundary can never be identified afterwards. Same reasoning as SW-ADR-013's currency snapshot.
- Closes OPEN-TZ-01.

---

*Ruled by the build session under `SW-ADR-015`'s standing delegation: a technical decision,
logged rather than escalated. The client may reverse it at any time. Recorded while
`CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
