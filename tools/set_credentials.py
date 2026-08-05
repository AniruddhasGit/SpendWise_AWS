#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write `.env` from prompts, without a password ever reaching a shell history.

    .venv/Scripts/python tools/set_credentials.py

Why a tool rather than "edit the file": the two connection strings have a trap
that produces an unhelpful error at connect time.

**asyncpg wants `?ssl=require`. It does NOT understand libpq's
`sslmode=require`** — that spelling is silently treated as an unknown server
setting and the connection fails with something that does not mention SSL. RDS
forces SSL, so every URL here needs the right one, and getting it wrong costs a
debugging session.

Passwords are prompted, never taken as arguments — an argument lands in shell
history and in the process list. `.env` is gitignored; this file writes nothing
anywhere else, and prints no secret back to the terminal.
"""
from __future__ import annotations

import getpass
import re
import secrets
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
EXAMPLE = ROOT / ".env.example"


def ask(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    got = input(f"  {label}{suffix}: ").strip()
    return got or default


def url_for(user: str, password: str, host: str, port: str, database: str) -> str:
    """Build a SQLAlchemy+asyncpg URL with the password percent-encoded.

    A password containing `@`, `/`, `:` or `#` breaks a naively-formatted URL —
    it parses as part of the host, and the error names a host nobody recognises.
    `quote` with an empty safe-list encodes all of them.
    """
    return (f"postgresql+asyncpg://{urllib.parse.quote(user, safe='')}:"
            f"{urllib.parse.quote(password, safe='')}@{host}:{port}/{database}"
            f"?ssl=require")


def main() -> int:
    print(__doc__.split("\n\n")[0])
    print()
    print("RDS connection details (the password is prompted, never echoed):")
    host = ask("endpoint (xxx.rds.amazonaws.com)")
    if not host:
        print("an endpoint is required.", file=sys.stderr)
        return 1
    port = ask("port", "5432")
    database = ask("database", "spendwise")

    print("\n  spendwise_owner — runs migrations, owns the tables")
    owner_pw = getpass.getpass("    password: ")
    print("  spendwise_app — serves traffic, owns nothing")
    app_pw = getpass.getpass("    password: ")
    if not owner_pw or not app_pw:
        print("both passwords are required.", file=sys.stderr)
        return 1

    print()
    admin_email = ask("BOOTSTRAP_ADMIN_EMAIL (an address NOBODY registers)",
                      "admin@spendwise.test")

    # A generated secret beats a typed one: 48 url-safe bytes clears the 32-byte
    # RFC 7518 floor with room, and nobody is tempted to reuse a memorable value.
    existing_secret = ""
    if ENV.is_file():
        m = re.search(r"^JWT_SECRET=(.+)$", ENV.read_text("utf-8"), re.M)
        if m and len(m.group(1)) >= 32 and "not-a-real-secret" not in m.group(1):
            existing_secret = m.group(1)
    jwt_secret = existing_secret or secrets.token_urlsafe(48)

    body = EXAMPLE.read_text("utf-8")
    body = re.sub(r"^DATABASE_URL=.*$",
                  "DATABASE_URL=" + url_for("spendwise_app", app_pw, host, port, database),
                  body, count=1, flags=re.M)
    body = re.sub(r"^MIGRATION_DATABASE_URL=.*$",
                  "MIGRATION_DATABASE_URL=" + url_for("spendwise_owner", owner_pw,
                                                      host, port, database),
                  body, count=1, flags=re.M)
    body = re.sub(r"^JWT_SECRET=.*$", "JWT_SECRET=" + jwt_secret, body, count=1, flags=re.M)
    body = re.sub(r"^BOOTSTRAP_ADMIN_EMAIL=.*$",
                  "BOOTSTRAP_ADMIN_EMAIL=" + admin_email, body, count=1, flags=re.M)

    ENV.write_text(body, encoding="utf-8", newline="\n")

    print(f"\nwrote {ENV.relative_to(ROOT)} — gitignored, never committed.")
    print("  DATABASE_URL           spendwise_app @ " + host)
    print("  MIGRATION_DATABASE_URL spendwise_owner @ " + host)
    print("  JWT_SECRET             " + ("kept from the existing file"
                                         if existing_secret else "generated, 48 bytes"))
    print("\nboth URLs carry ?ssl=require — asyncpg's spelling, not libpq's.")
    print("\nnext:  .venv/Scripts/python tools/check_rds.py --host %s --user spendwise_owner"
          % host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
