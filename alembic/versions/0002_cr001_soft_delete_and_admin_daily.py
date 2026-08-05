"""CR-001: soft account deletion, and the administrator's daily spending function.

Revision ID: 0002_cr001
Revises: 0001_baseline

**Idempotent in both directions, and that is the whole design of this file.**

`0001_baseline` is GENERATED from `docs/06 DataModel/datamodel.json`, and that
file now carries `users.deleted_at` and `admin_user_daily()` — so a database
built from scratch gets both from the baseline and never needs this migration's
contents. A database already stamped at `0001` will never re-run it and needs
exactly this.

Both are true at once, so every statement here is `IF NOT EXISTS` or
`CREATE OR REPLACE`: running it against a fresh database is a no-op, running it
against an existing one is the change. The alternative — freezing the baseline
and putting the column only here — was rejected because it makes the generated
schema stop describing the schema, and `generate.py --check` is the thing that
keeps `datamodel.json` honest.

The function body is not typed here. It is EXTRACTED from the generated
`security.sql` at migration time, so the deployed function and the spec of
record cannot differ — the same rule `tools/apply_function.py` follows.
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision: str = "0002_cr001"
down_revision: str | None = "0001_baseline"
branch_labels = None
depends_on = None

SECURITY = (Path(__file__).resolve().parents[2]
            / "docs" / "06 DataModel" / "security.sql")


def _function(name: str) -> str:
    """The generated `CREATE OR REPLACE FUNCTION …$fn$;` block, by name.

    Read rather than transcribed. A copy in this file would be a second
    definition of a `SECURITY DEFINER` function, and the failure mode of two
    definitions is that the database runs the older one while the spec of
    record describes the newer.
    """
    sql = SECURITY.read_text(encoding="utf-8")
    start = sql.index(f"CREATE OR REPLACE FUNCTION {name}(")
    end = sql.index("$fn$;", start) + len("$fn$;")
    return sql[start:end]


def upgrade() -> None:
    # SOFT deletion (`SW-ADR-150`). NULL means live, so the common case needs no
    # predicate and a forgotten one fails OPEN — a closed account showing up is
    # a visible bug; a live account vanishing is a support ticket nobody can
    # diagnose.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL")

    # PARTIAL, like `ix_sessions_revoked_at`: live accounts are what every
    # request looks up, closed ones accumulate forever, and indexing them would
    # grow the index without it ever being read.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_users_deleted_at__where_deleted_at_is_null "
        "ON users (deleted_at) WHERE deleted_at IS NULL")

    # `SW-ADR-151`. Three columns and no fourth — see the function's own
    # comment in security.sql. `CREATE OR REPLACE` is idempotent, and re-running
    # the other three costs nothing while guaranteeing that a database stamped
    # before `SW-ADR-149` gets the GUC-swapping versions rather than the ones
    # that silently returned nothing.
    for name in ("admin_expense_stats", "admin_user_sessions",
                 "admin_revoke_sessions", "admin_user_daily"):
        op.execute(_function(name))
    op.execute("GRANT EXECUTE ON FUNCTION admin_user_daily(BIGINT, DATE, DATE) "
               "TO spendwise_app")


def downgrade() -> None:
    """Drops the function and the index. **It does NOT drop the column.**

    `deleted_at` is the only record that an account was closed, and closing is
    the thing a person asked for. A downgrade that erased it would turn every
    closed account back into a live one — sign-in restored, silently, for people
    who deliberately left. Dropping a column is not the inverse of adding one
    when the column holds a decision somebody made.
    """
    op.execute("DROP FUNCTION IF EXISTS admin_user_daily(BIGINT, DATE, DATE)")
    op.execute("DROP INDEX IF EXISTS ix_users_deleted_at__where_deleted_at_is_null")
