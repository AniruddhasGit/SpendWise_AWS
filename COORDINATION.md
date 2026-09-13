# COORDINATION.md — live map for parallel work

Read this when **two or more sessions run at once**. On this project that is the normal case:
a build session writes application code while a DevOps session builds AWS by hand.

When only one session is running, this file is informational.

---

## The two standing lanes

| Lane | Owner | Owns | Never touches |
|---|---|---|---|
| **BUILD** | the application session | `app/**` · `client/**` · `alembic/**` · `docs/**` · `tests/**` | anything in AWS · `.github/workflows/**` · any Dockerfile until `SW-ADR-011` releases it |
| **OPS** | the client's separate DevOps session | AWS console and CLI · `.github/workflows/**` · `docs/30 Deployment/AWS_PREP_QUEUE.md` tick-offs | `app/**` · `client/**` · `alembic/**` |

**The lanes are disjoint by design** (`SW-ADR-005` (superseded by `SW-ADR-155`, 2026-09-13)). The build session creates nothing in AWS; the DevOps
session writes no application code. Where they meet is exactly two files:

- **`docs/30 Deployment/AWS_PREP_QUEUE.md`** — BUILD writes the requests, OPS marks them done and records what was
  actually created.
- **`.env.example`** — BUILD adds the keys the app needs; OPS supplies the real values into `.env`
  (gitignored) or SSM.

## The handshake

**BUILD → OPS.** Anything needed from AWS is added to the AWS prep queue with a "needed by" stage,
**and** said in chat, early enough to be prepared while code is still being written. Never announce a
dependency on the day it blocks.

**OPS → BUILD.** When an item is created, report **what actually exists** — endpoint, version,
role name, region. The build session may then write it down as observed. Under K1 it cannot write
"the RDS instance exists" because the item is on a list; only because someone said it does.

## Standing facts about the boundary

- The build session **never observes the app running in any AWS environment.** Every statement it
  makes about AWS behaviour is **reasoned, not observed**, and is labelled that way.
- The deployed environment is **never called production** in any document while it runs without TLS
  (`SW-ADR-014`).
- **Destructive AWS actions are always human.** No session, in either lane, deletes a database,
  drops a bucket, or rotates a credential.

## Shared-primitive locks

Claim a shared file **before** editing it; release when done. Both lanes append here.

```
claim log:  <file>  ->  <lane>  @ <time>   (released <time>)
```

*(none open)*

## Rule

A change to the shared spine after the lanes have forked — the data model, the environment
contract, the module layout — is a **stop-the-world**. Announce it here, and the other lane
re-reads before continuing.
