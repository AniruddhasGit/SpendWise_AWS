# Failure modes

> **UNVERIFIED — reasoned, not observed.** The build session creates nothing in AWS and
> never watches this run (`SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13)). Only the client can turn any AWS claim below into
> evidence.

| What breaks | The person sees | The log says | Detected by |
|---|---|---|---|
| Database unreachable at boot | nothing — no task | ERROR naming the revision reached vs target | ECS restart loop → running-task alarm |
| Migration fails mid-chain | nothing | ERROR with both revisions | same. **No retry** — an indefinite hang would otherwise be the default |
| Catalog assertion fails | nothing | ERROR naming which of the three failed | startup abort. This is the guard that stops a silent isolation collapse |
| Signing secret rotated | signed out | INFO "JWT secret rotated — N sessions revoked" | automatic; the dashboard never reports phantom sessions |
| Summary request fails | **error panel with retry, period preserved** | WARN | the person. **Never zeros** — in a money app a rendered 0.00 is indistinguishable from a true zero |
| Session revoked mid-use | reason banner at sign-in | INFO | one interceptor; **duplicate redirects suppressed** because the dashboard fires more than one request |
| Storage unconfigured | control hidden | WARN at startup naming the disabled feature | `receipts_enabled: false` |
| Upload abandoned | nothing | — | the staging prefix expires after one day |
| Rate limit tripped | 429 with a countdown | WARN | the person — otherwise they retry and extend the block |
| Deploy in progress | the site is down | — | **expected.** One instance, one port |

**The failure with no detector:** the instance is up, the container is healthy, and the
application is wrong. Nothing here catches that — only the test suite does, before it ships.
