"""Test fixtures. The database ones run against **real RDS**, never a fake.

`SW-ADR-008` ruled that the build happens against real RDS, so a fake repository
here would give a green suite and a false one — on the single guarantee this
product is about. Tests that need a database are marked `db` and skip cleanly
when `spendwise_test` is unreachable, so a laptop with no network still runs the
pure tests.

Per-case reset is `TRUNCATE … RESTART IDENTITY CASCADE` on an **owner**
connection owned by this fixture (`CV-24`). Two things make the usual
outer-transaction-and-rollback pattern unavailable:

* it contradicts `CV-12` — the session dependency commits, once, per request;
* `set_config('app.user_id', …, true)` is transaction-local, so nesting the
  request inside an outer transaction stops the GUC's lifetime matching the
  request's.

`RESTART IDENTITY` is not optional. `expected_summary.json` names `category_id`
1, 3 and 5, which are only person A's Groceries/Transport/Health if A's eight
categories take identity values 1–8. Without it the second test case gets 17–24
and every `by_category` assertion fails for a reason unrelated to the code.
"""
from __future__ import annotations

import os
import re
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio


def redact(url: str) -> str:
    """`postgresql+asyncpg://u:secret@host/db` -> `postgresql+asyncpg://u:***@host/db`."""
    return re.sub(r"://([^:/@]+):[^@]*@", lambda m: f"://{m.group(1)}:***@", url)


class SecretUrl(str):
    """A connection URL that does not print its password.

    It IS a `str` — `monkeypatch.setenv`, `create_async_engine` and the seeder's
    `TEST_DB in url` guard all keep working unchanged. Only `repr()` differs,
    and `repr()` is what pytest calls: **every failure report lists the fixture
    values of the failing test**, so one broken assertion put the RDS password
    into the output. A failing test is exactly when that output gets pasted into
    an issue, a chat or a CI log — and a secret that has reached a log has left
    the `.env` whatever `.gitignore` says.

    Redacting the value itself was the first attempt and broke the whole suite:
    the `client` fixture connects with this string.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f"SecretUrl({redact(self)!r})"


# The test database is a SEPARATE database in the same instance (SW-ADR-068), so
# RLS stays real for every test and nothing here can touch the dev data.
TEST_DB = "spendwise_test"

TABLES = ("expenses", "categories", "sessions", "password_resets",
          "admin_audit_log", "users", "app_meta")


def _swap_db(url: str) -> str:
    return re.sub(r"/(?:spendwise)(\?|$)", f"/{TEST_DB}\\1", url, count=1)


@pytest.fixture(scope="session")
def test_urls() -> tuple[SecretUrl, SecretUrl] | None:
    """`(runtime_url, owner_url)` pointed at `spendwise_test`, or None."""
    from app.core.settings import get_settings
    try:
        s = get_settings()
    except SystemExit:
        return None
    return (SecretUrl(_swap_db(s.DATABASE_URL.get_secret_value())),
            SecretUrl(_swap_db(s.MIGRATION_DATABASE_URL.get_secret_value())))


@pytest_asyncio.fixture
async def clean_db(test_urls) -> AsyncIterator[SecretUrl]:
    """Truncate as the OWNER, then hand back the RUNTIME url.

    The owner does the reset because `spendwise_app` holds no `DELETE` on
    `users` and `verify_invariants.sql` asserts it cannot — the runtime role
    genuinely cannot perform this, by design (`SW-ADR-137`).
    """
    if test_urls is None:
        pytest.skip("no database configured")
    runtime_url, owner_url = test_urls

    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    owner = create_async_engine(owner_url, poolclass=None)
    try:
        async with owner.begin() as conn:
            await conn.execute(text(
                f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
    except Exception as exc:                       # noqa: BLE001
        await owner.dispose()
        pytest.skip(f"{TEST_DB} unreachable or not migrated: {type(exc).__name__}")
    await owner.dispose()

    yield runtime_url


@pytest_asyncio.fixture
async def client(clean_db, monkeypatch) -> AsyncIterator:
    """An httpx client bound to the app, against the test database.

    In-process via ASGITransport — no port, no server, and the same code path a
    real request takes (`CV-16`).
    """
    import httpx

    monkeypatch.setenv("DATABASE_URL", clean_db)
    monkeypatch.setenv("SPENDWISE_DOTENV", "0")
    # E1-S6: the limiter is ON in production and OFF here. A suite that signs in
    # more than ten times a minute would otherwise start failing at its eleventh
    # request, and the failure would read as a product bug rather than as the
    # throttle doing its job. `tests/test_rate_limits.py` turns it back on and is
    # the only place that asserts its behaviour.
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")

    from app.core.settings import get_settings
    import app.core.db as db_mod

    get_settings.cache_clear()
    db_mod._engine = None

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport,
                                 base_url="http://testserver") as c:
        yield c

    if db_mod._engine is not None:
        await db_mod._engine.dispose()
        db_mod._engine = None
    get_settings.cache_clear()
