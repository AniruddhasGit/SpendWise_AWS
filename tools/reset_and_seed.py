#!/usr/bin/env python3
"""Wipe the DEV database and create two accounts: one person, one administrator.

    py tools/reset_and_seed.py

**This destroys every row in `spendwise`.** It refuses to run against any other
database name, and it prints what it is about to remove before it does it.

Why a tool and not `tests/seed`: that seeder lives under the test tree and
`SW-ADR-086` forbids it running anywhere but `spendwise_test`, because it uses
published passwords. This one is for the DEV database the client actually looks
at, so it generates its own passwords, shows them **once**, and writes them
nowhere.

The administrator is created through `BOOTSTRAP_ADMIN_EMAIL` rather than by an
`UPDATE`: `SRC-001 §4.4` says the first account in a fresh database becomes an
admin when it matches the configured address, and using the real path means the
`bootstrap_admin_claimed` audit row exists and the mechanism is exercised
rather than bypassed.
"""
from __future__ import annotations

import asyncio
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TABLES = ("expenses", "categories", "sessions", "password_resets",
          "admin_audit_log", "users", "app_meta")

# Readable and long. Four words from a small list is not a passphrase scheme —
# it is a starting password for two accounts on a development instance, shown
# once, changeable from Settings. `secrets`, never `random`.
WORDS = ("harbour", "lantern", "meadow", "cobalt", "pepper", "willow", "quartz",
         "cinder", "marble", "thicket", "sable", "juniper", "amber", "kestrel")


def passphrase() -> str:
    return "-".join(secrets.choice(WORDS) for _ in range(4))


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def wipe(owner_url: str) -> dict:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(owner_url, poolclass=None)
    counts = {}
    async with engine.connect() as c, c.begin():
        counts["users"] = (await c.execute(text("SELECT count(*) FROM users"))).scalar()
        counts["sessions_all"] = (await c.execute(
            text("SELECT count(*) FROM sessions"))).scalar()
    async with engine.begin() as c:
        await c.execute(text(
            f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
    await engine.dispose()
    return counts


async def main() -> int:
    from app.core.settings import get_settings

    s = get_settings()
    runtime = s.DATABASE_URL.get_secret_value()
    owner = s.MIGRATION_DATABASE_URL.get_secret_value()

    if "/spendwise?" not in runtime and "/spendwise" not in runtime.split("?")[0][-11:]:
        print(f"refusing: DATABASE_URL does not point at `spendwise`")
        return 1
    if "spendwise_test" in runtime:
        print("refusing: DATABASE_URL points at the TEST database. "
              "Use the test fixtures for that one.")
        return 1

    before = await wipe(owner)
    print(f"  wiped spendwise — removed {before['users']} account(s), "
          f"{before['sessions_all']} session row(s), and everything they owned")

    admin_email = "admin@spendwise.app"
    user_email = "you@spendwise.app"
    admin_pw, user_pw = passphrase(), passphrase()

    port = free_port()
    env = {**os.environ,
           "DATABASE_URL": runtime, "MIGRATION_DATABASE_URL": owner,
           "JWT_SECRET": s.JWT_SECRET.get_secret_value(),
           "SPENDWISE_DOTENV": "0",
           # `SRC-001 §4.4`: the first account matching this address, in a
           # database with zero admins, claims the administrator role — through
           # the real registration path, so the audit row exists.
           "BOOTSTRAP_ADMIN_EMAIL": admin_email,
           "COOKIE_SECURE": "false", "LOG_LEVEL": "WARNING"}

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    base = f"http://127.0.0.1:{port}"
    try:
        import urllib.request
        for _ in range(160):
            try:
                with urllib.request.urlopen(f"{base}/healthz", timeout=2) as r:
                    if r.status == 200:
                        break
            except Exception:                              # noqa: BLE001
                time.sleep(0.25)
        else:
            print("the server never became healthy")
            return 1

        import httpx

        async with httpx.AsyncClient(base_url=base, timeout=30) as c:
            # The ADMIN first — the bootstrap claim only fires while the
            # administrator count is zero, so order is load-bearing.
            r = await c.post("/api/auth/register", json={
                "email": admin_email, "password": admin_pw,
                "display_name": "Site Administrator"})
            r.raise_for_status()
            admin = r.json()
            if admin["role"] != "admin":
                print(f"  the bootstrap claim did not fire — role is {admin['role']!r}")
                return 1
            await c.post("/api/auth/logout")

            r = await c.post("/api/auth/register", json={
                "email": user_email, "password": user_pw,
                "display_name": "Aniruddha"})
            r.raise_for_status()
            person = r.json()
            assert person["role"] == "user", "the second account claimed admin"

            # A little spending, so the dashboard has something to draw. Through
            # the real endpoint, so every validation rule applies.
            from datetime import date, timedelta
            today = date.today()
            sample = [
                ("2450.00", 1, "Weekly groceries", 1),
                ("380.50", 2, "Lunch with the team", 1),
                ("120.00", 3, "Auto to office", 2),
                ("18500.00", 4, "Rent", 4),
                ("899.00", 5, "Pharmacy", 5),
                ("640.00", 6, "Cinema", 6),
                ("3299.00", 7, "Running shoes", 8),
                ("75.00", 3, "Metro card top-up", 9),
                ("1150.00", 2, "Dinner out", 11),
                ("260.00", 1, "Vegetables", 12),
                ("4999.00", 7, "Headphones", 14),
                ("95.00", None, None, 15),
            ]
            made = 0
            for amount, cat, note, ago in sample:
                when = today - timedelta(days=ago)
                body = {"amount": amount, "spent_on": when.isoformat()}
                if cat is not None:
                    # The person's categories are 9-16: the admin registered
                    # first and took 1-8.
                    body["category_id"] = 8 + cat
                if note:
                    body["description"] = note
                rr = await c.post("/api/expenses", json=body)
                if rr.status_code == 201:
                    made += 1
                else:
                    print(f"    (skipped {amount}: {rr.status_code} {rr.text[:80]})")
            await c.post("/api/auth/logout")

        print(f"  created 2 accounts and {made} sample expenses")
        print("")
        print("  " + "=" * 62)
        print(f"  ADMINISTRATOR   {admin_email}")
        print(f"  password        {admin_pw}")
        print("")
        print(f"  PERSON          {user_email}")
        print(f"  password        {user_pw}")
        print("  " + "=" * 62)
        print("")
        print("  Shown once. They are written to no file - change them from")
        print("  Settings, or re-run this to generate new ones.")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
