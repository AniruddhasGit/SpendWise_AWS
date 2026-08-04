# SW-ADR-017 — Modular monolith: a module touches only its own tables

| Field | Value |
|---|---|
| ADR | `SW-ADR-017` |
| Pack | `SPENDWISE_V1` |
| Type | ARCHITECTURE |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Decided by | CLIENT |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SRC-001 S3.4` · `SRC-001 S3.5` · `SRC-001 S7.4` |

## Context

SRC-001 S3.4 states the rule the client actually cares about: a module calls another module's service rather than querying its tables. But SRC-001 S7.4 also requires the whole dashboard in one round trip, and the category breakdown needs names that live in another module's table. The two requirements collide.

## Options considered

- A. Allow read-only cross-module joins between FK-linked tables.
- B. The repository returns ids and totals; the SERVICE asks the other module's service for names and stitches in Python.

## Decision

**B, with the module rule intact.**

## Consequences

- The expenses repository returns category_id plus totals. The expenses SERVICE calls the categories service for names.
- Still ONE round trip for the browser - which is what SRC-001 S7.4 actually asks for. It asks for one request, not one SQL statement.
- Layering enforced: routers never write queries; repositories never know what HTTP is; the service translates between Pydantic schemas and SQLAlchemy models.
- The shared folder is core, never platform - a top-level package named platform shadows the standard library module (SRC-001 S3.5).

---

*Accepted decisions are immutable. A reversal happens by a new superseding record, never by editing
this file. Recorded while `CONSTITUTION.md` was UNADOPTED — see `OPEN-NAME-01`.*
