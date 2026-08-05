# SW-ADR-016 — Stack lock

> **⚠ EXTENDED 2026-08-05 by `SW-ADR-139` (`CV-16`).** This record locked the runtime
> stack and said *do not substitute* — but named **no test tool**, while Art IX.1
> mandates failing-test-first and `E0-S5` mandates a real browser. The first engineer
> therefore had to extend a stack this record forbids extending. The test stack is
> **pytest · pytest-asyncio · httpx (ASGITransport) · Playwright**, and it is locked
> on the same terms as the rest.

| Field | Value |
|---|---|
| ADR | `SW-ADR-016` |
| Pack | `SPENDWISE_V1` |
| Type | ARCHITECTURE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S2` |

## Context

SRC-001 S2 fixes the entire technology stack and states: 'I've already decided these. Please don't substitute alternatives, even better ones.' Recorded as an ADR so it is citable and so no later session re-opens it.

## Options considered

- A. The stack as written in SRC-001 S2.
- B. Any substitution - explicitly refused by the client.

## Decision

**A. Python 3.12 / FastAPI / uvicorn / SQLAlchemy 2.0 async + asyncpg / Alembic / Pydantic v2 / PyJWT / bcrypt / boto3; React 18 + Vite, plain CSS, no UI framework; PostgreSQL on RDS; S3 for receipt images only.**

## Consequences

- FROZEN. Never re-opened, never substituted, however attractive an alternative looks.
- A proposal to change any element is a new superseding ADR with the client's ruling, not a code review comment.

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
