#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify an RDS instance is set up the way the day-one gate needs it.

Run this **after** `docs/30 Deployment/rds_bootstrap.sql` and **before** telling
the build session the instance is ready. It answers, one line each, the six
questions that otherwise surface as a confusing failure an hour later.

    py tools/check_rds.py --host YOUR.rds.amazonaws.com --user spendwise_owner

It prompts for the password rather than taking it on the command line, because a
password in a command line ends up in your shell history.

Every check names what to do when it fails. Nothing here writes anything.
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

try:
    import asyncpg
except ImportError:                                     # pragma: no cover
    print("asyncpg is not installed. Run this with the project venv:\n"
          "    .venv/Scripts/python tools/check_rds.py ...", file=sys.stderr)
    raise SystemExit(1)

OK, BAD, WARN = "  ok  ", " FAIL ", " warn "


class Result:
    def __init__(self) -> None:
        self.failed = 0

    def check(self, ok: bool, label: str, detail: str = "", fix: str = "") -> None:
        print(f"[{OK if ok else BAD}] {label}" + (f"  — {detail}" if detail else ""))
        if not ok:
            self.failed += 1
            if fix:
                for line in fix.split("\n"):
                    print(f"         → {line}")

    def note(self, label: str, detail: str) -> None:
        print(f"[{WARN}] {label}  — {detail}")


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", required=True, help="the RDS endpoint")
    ap.add_argument("--port", type=int, default=5432)
    ap.add_argument("--user", required=True, help="spendwise_owner, or the master user")
    ap.add_argument("--database", default="spendwise")
    args = ap.parse_args()

    password = getpass.getpass(f"password for {args.user}: ")
    r = Result()

    print(f"\nconnecting to {args.host}:{args.port}/{args.database} as {args.user}\n")

    try:
        # ssl="require" is how asyncpg spells it. NOT libpq's sslmode= — RDS
        # forces SSL and the wrong spelling fails with an unhelpful error.
        conn = await asyncio.wait_for(
            asyncpg.connect(host=args.host, port=args.port, user=args.user,
                            password=password, database=args.database, ssl="require"),
            timeout=20,
        )
    except asyncio.TimeoutError:
        print(f"[{BAD}] cannot reach {args.host}:{args.port} — timed out")
        print("         → the security group almost certainly does not allow YOUR IP.")
        print("         → prep-queue item 4: inbound PostgreSQL/TCP 5432, source = your IP.")
        print("         → your home IP changes; if this worked yesterday, check this first.")
        return 1
    except Exception as exc:                            # noqa: BLE001
        print(f"[{BAD}] connection refused — {type(exc).__name__}: {exc}")
        print("         → wrong password, wrong database name, or the role does not exist.")
        print("         → if the database is missing, rds_bootstrap.sql has not been run.")
        return 1

    try:
        # 1. version
        version = await conn.fetchval("SHOW server_version")
        major = version.split(".")[0]
        r.check(int(major) >= 14, f"PostgreSQL {version}",
                "minimum is 14 (datamodel.json)",
                "the schema needs FORCE ROW LEVEL SECURITY and generate_series")
        r.note("version parity",
               f"local development is on 18.x. RDS is {major}. What matters is that "
               f"they AGREE — a difference shows up once, in production, in "
               f"something nobody tested.")

        # 2. SSL is actually in use
        ssl_on = await conn.fetchval(
            "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
        r.check(bool(ssl_on), "the connection is encrypted",
                "RDS forces SSL",
                "if this is false the connection string is wrong; asyncpg wants "
                "?ssl=require, not libpq's sslmode=require")

        # 3. both roles exist, with the right attributes
        roles = {row["rolname"]: row for row in await conn.fetch(
            "SELECT rolname, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb "
            "FROM pg_roles WHERE rolname LIKE 'spendwise%'")}
        for name in ("spendwise_owner", "spendwise_app"):
            row = roles.get(name)
            r.check(row is not None, f"role {name} exists", "",
                    "run docs/30 Deployment/rds_bootstrap.sql as the master user")
            if row:
                safe = not (row["rolsuper"] or row["rolbypassrls"]
                            or row["rolcreaterole"] or row["rolcreatedb"])
                r.check(safe, f"role {name} holds no dangerous attribute",
                        f"super={row['rolsuper']} bypassrls={row['rolbypassrls']} "
                        f"createrole={row['rolcreaterole']} createdb={row['rolcreatedb']}",
                        "BYPASSRLS on the runtime role would make the isolation gate "
                        "pass for the wrong reason, which is worse than failing")

        # 4. both databases exist and are owned by the owner role
        dbs = {row["datname"]: row["owner"] for row in await conn.fetch(
            "SELECT datname, pg_get_userbyid(datdba) AS owner "
            "FROM pg_database WHERE datname LIKE 'spendwise%'")}
        for name in ("spendwise", "spendwise_test"):
            r.check(name in dbs, f"database {name} exists", "",
                    "rds_bootstrap.sql creates both; SW-ADR-068 needs the test one "
                    "so RLS stays real for every test")
            if name in dbs:
                r.check(dbs[name] == "spendwise_owner",
                        f"database {name} is owned by spendwise_owner",
                        f"owner is {dbs[name]}",
                        "PG15+ no longer grants CREATE on public to PUBLIC — the "
                        "owner needs to own the database to own its public schema")

        # 5. has the schema been applied yet?
        tables = await conn.fetchval(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema = 'public'")
        if tables:
            r.note("schema", f"{tables} tables already present — "
                             f"`alembic upgrade head` has run")
        else:
            r.note("schema", "empty, as expected before the first migration")

    finally:
        await conn.close()

    print()
    if r.failed:
        print(f"{r.failed} check(s) failed. Fix those before the build session connects —")
        print("each one is a guarantee the day-one gate rests on.")
        return 1
    print("All checks passed. Send the build session: endpoint, port, "
          "Postgres major version, master username. NOT the password.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
