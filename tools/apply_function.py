#!/usr/bin/env python3
"""Re-apply the admin SECURITY DEFINER functions to both databases.

A one-off: the baseline migration is already stamped, so `alembic upgrade` will
not re-run it, and `CREATE OR REPLACE FUNCTION` is idempotent. Extracted from
the GENERATED `security.sql` rather than typed here, so the deployed function
and the spec of record cannot differ.

    py tools/apply_function.py
"""
from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SECURITY = ROOT / "docs" / "06 DataModel" / "security.sql"


def statements() -> list[str]:
    """Every `CREATE OR REPLACE FUNCTION ... $fn$;` block, in file order.

    Found by scanning rather than by naming them, so a function added to
    `datamodel.json` is applied without this script being edited — the failure
    that shape prevents is a new definer function that exists in the spec, in
    the migration, and nowhere in the running database.

    Scoped to `admin_*`, which is what the `$fn$` tag delimits. `security.sql`
    also defines `audit_log_is_append_only()`, a trigger function quoted with
    plain `$$` — scanning for every `CREATE OR REPLACE FUNCTION` walked into it
    looking for a `$fn$` terminator that is not there.
    """
    sql = SECURITY.read_text(encoding="utf-8")
    out, at = [], 0
    while True:
        start = sql.find("CREATE OR REPLACE FUNCTION admin_", at)
        if start < 0:
            return out
        end = sql.index("$fn$;", start) + len("$fn$;")
        out.append(sql[start:end])
        at = end


async def main() -> int:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.core.settings import get_settings

    fns = statements()
    assert fns, "no functions found in security.sql"
    for fn in fns:
        assert "plpgsql" in fn and "set_config" in fn, "extracted the wrong block"

    base = get_settings().MIGRATION_DATABASE_URL.get_secret_value()
    for db in ("spendwise", "spendwise_test"):
        engine = create_async_engine(base.replace("/spendwise?", f"/{db}?"), poolclass=None)
        async with engine.begin() as c:
            for fn in fns:
                await c.execute(text(fn))
        await engine.dispose()
        print(f"  redefined {len(fns)} function(s) on {db}")

    engine = create_async_engine(base.replace("/spendwise?", "/spendwise_test?"),
                                 poolclass=None)
    async with engine.connect() as c, c.begin():
        await c.execute(text("SELECT set_config('app.user_id', '1', true)"))
        for target in (1, 2):
            row = (await c.execute(text("SELECT * FROM admin_expense_stats(:u)"),
                                   {"u": target})).one()
            print(f"  as user 1, stats for user {target}: {tuple(row)}")
        back = (await c.execute(
            text("SELECT current_setting('app.user_id', true)"))).scalar()
        print(f"  app.user_id restored to: {back!r}")
    await engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
