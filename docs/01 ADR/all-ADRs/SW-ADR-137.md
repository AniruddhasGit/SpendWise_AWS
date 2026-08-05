# SW-ADR-137 — Table privileges are in the spec of record, and the invariant check verifies them

| Field | Value |
|---|---|
| ADR | `SW-ADR-137` |
| Pack | `SPENDWISE_V1` |
| Type | REMEDIATION |
| Decision status | **APPROVED** |
| Decision outcome | APPROVED_FOR_IMPLEMENTATION |
| Supersedes | — |
| Raised by | GOAL_13 uncoached slice run 2, GUESS #13 (BLOCKING) |
| Decided by | BUILD_SESSION (under `SW-ADR-015`) |
| Decision date | 2026-08-05 |
| Release decision | RELEASE |
| Release status | RELEASED |
| Sources | `SW-ADR-081` · `SW-ADR-066` · `permissions.tsv` · `verify_invariants.sql` |

## Context

**`security.sql` contained no `GRANT` on any table.** Its only privilege statements were
`REVOKE UPDATE, DELETE ON admin_audit_log` and `GRANT EXECUTE` on the stats function. The runtime
role `spendwise_app` therefore held **no privilege on any table**, and every query in the
application would have failed with `permission denied`.

The part that makes this worth a record rather than a one-line fix: **`verify_invariants.sql`
would still have printed all-green.** It checks that the runtime role owns no table, is not
superuser and holds no `BYPASSRLS` — three things about what the role *cannot* do. Nothing checked
that it *can* do anything. A boot assertion that only tests the negative direction passes happily
against a role that cannot read a single row.

`permissions.tsv` describes a persona matrix — `user | expenses | read/write | own rows only` —
which reads like an authorisation model and is enforced by nothing: `users` has no RLS
(`SW-ADR-097`) and no grant, so "own row only" was true only because *no* row was reachable.

## Decision

**Privileges live in `datamodel.json` and are generated into `security.sql`**, like everything
else in that package:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON expenses, categories, sessions TO spendwise_app;
GRANT SELECT, INSERT, UPDATE          ON users, password_resets       TO spendwise_app;
GRANT SELECT, INSERT                  ON admin_audit_log              TO spendwise_app;
GRANT SELECT, UPDATE                  ON app_meta                     TO spendwise_app;
GRANT USAGE ON SCHEMA public TO spendwise_app;
```

**No `DELETE` on `users`** — there is no user-deletion path in v1 (`SW-ADR-107`), so the privilege
would be capability the design does not want. **No `DELETE` on `admin_audit_log`** — already
revoked, and stated positively here so the two cannot drift apart. `password_resets` gets no
`DELETE` either; `SW-ADR-122` prunes it, and pruning runs as the owner.

**`verify_invariants.sql` gains the positive direction**: it asserts the runtime role *holds* each
privilege above, not merely that it lacks the dangerous ones.

## Consequences

- **Row-level security only narrows what a grant already allows.** With no grant, RLS was
  protecting a door that was already welded shut — which is why nothing downstream noticed.
- `permissions.tsv` stays a persona matrix and now says so; it is documentation of intent, and
  `security.sql` is the enforcement.
- The privilege list is deliberately narrower than "ALL": every verb it omits is a verb the
  application has no path for.
