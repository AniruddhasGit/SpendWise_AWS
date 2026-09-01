"""Browser fixtures — a real uvicorn on a real port, driven by a real Chromium.

`CONSTITUTION` Art IX.4 requires the day-one proof watched in a **real
browser**. Everything else in this suite goes through `httpx.ASGITransport`,
which is the same code path but not the same evidence: it never binds a socket,
never parses a `Set-Cookie` header, never enforces `httpOnly`, and never runs a
line of the client. Most of what this directory proves is invisible to it.

So this starts the actual server, with `client/dist` mounted, against
`spendwise_test`, and points Chromium at it.

**Playwright's ASYNC api, not the sync one.** The sync API drives a greenlet
loop and refuses to run inside an asyncio event loop — and `asyncio_mode =
"auto"` means every test in this repository is already inside one. The sync API
was tried first and failed with `Runner.run() cannot be called from a running
event loop`, which is that collision, not a fixture bug.

The date is frozen to **2026-08-05** on both sides: `APP_TODAY_OVERRIDE` for
the server and `window.__SPENDWISE_TODAY__` for the client. `SW-ADR-039` fixes
the gate to that day, and 75810 is only 75810 if `days_elapsed` is 5.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import pytest_asyncio

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "client" / "dist" / "index.html"
GATE_DAY = "2026-08-05"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def app_server(test_urls):
    """A uvicorn subprocess serving the API **and the built client**.

    A subprocess rather than a thread: `app.main` reads settings at IMPORT, and
    the in-process suite has already imported it against a different
    `DATABASE_URL`. Re-importing in a thread would give one of the two the
    other's configuration, non-deterministically.
    """
    if test_urls is None:
        pytest.skip("no database configured")
    if not DIST.is_file():
        pytest.skip("client/dist is not built — run `npm run build` in client/")

    from app.core.settings import get_settings

    runtime_url, owner_url = test_urls
    port = _free_port()
    settings = get_settings()

    env = {
        **os.environ,
        "DATABASE_URL": str(runtime_url),
        # Handed through the child's ENVIRONMENT, never its argv: a command line
        # is visible to every process on the machine and lands in shell history,
        # and this one carries the signing secret.
        "MIGRATION_DATABASE_URL": str(owner_url),
        "JWT_SECRET": settings.JWT_SECRET.get_secret_value(),
        # `.env` is NOT read by the child. It points at the DEV database, and a
        # browser test that seeded two people with published passwords into dev
        # would be the worst kind of green.
        "SPENDWISE_DOTENV": "0",
        # The gate's day, on the SERVER side. `days_elapsed` is computed from
        # it, and 379049 / 5 is 75810 only on this date.
        "APP_TODAY_OVERRIDE": GATE_DAY,
        "COOKIE_SECURE": "false",   # no TLS on 127.0.0.1 (`SW-ADR-014`)
        # OFF, for the same reason `settings.py` gives for the in-process suite:
        # a test that registers eleven accounts must not fail for a reason
        # unrelated to what it asserts. `SPENDWISE_DOTENV=0` above means the
        # child never reads `.env`, so without this line the field falls back to
        # its default of TRUE and `RATE_LIMIT_REGISTER_PER_MIN=5` refuses the
        # sixth account of every run. The limits themselves are covered
        # in-process by `test_rate_limits.py`; nothing here is weakened.
        #
        # This fixture predates `E1-S6`, which added rate limiting, and the
        # browser suite was not re-run afterwards — which is why the whole
        # browser half had never passed.
        "RATE_LIMIT_ENABLED": "false",
        "LOG_LEVEL": "INFO",
        "EXPOSE_VERSION": "browser-test",
    }

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 45
    import urllib.error
    import urllib.request
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"uvicorn exited {proc.returncode}:\n{proc.stdout.read()}")
        try:
            with urllib.request.urlopen(f"{base}/healthz", timeout=2) as r:
                if r.status == 200:
                    break
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(0.25)
    else:
        proc.kill()
        raise RuntimeError("uvicorn never became healthy")

    yield base

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest_asyncio.fixture
async def browser():
    """Function-scoped, deliberately.

    A session-scoped browser wants `loop_scope="session"`, and `clean_db` — which
    almost every test here also needs — lives on the per-test loop. Mixing loop
    scopes in one test does not error; it HANGS, which cost a 600-second timeout
    to diagnose. Chromium launches in about a third of a second, and that is a
    much better trade than a fixture graph nobody can reason about.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        b = await p.chromium.launch()
        yield b
        await b.close()


async def _context(browser, base_url, **kw):
    ctx = await browser.new_context(
        base_url=base_url, locale="en-IN", timezone_id="Asia/Kolkata", **kw)
    # An INIT SCRIPT, so it runs before any page script. Setting it after load
    # would let the first render compute a period from the real date and then
    # silently disagree with the server.
    await ctx.add_init_script(f"window.__SPENDWISE_TODAY__ = '{GATE_DAY}';")
    return ctx


@pytest_asyncio.fixture
async def page(browser, app_server):
    """A fresh, isolated context per test — so no cookie survives between them."""
    ctx = await _context(browser, app_server, viewport={"width": 1280, "height": 900})
    pg = await ctx.new_page()

    # Any uncaught client error fails the test that caused it. Without this a
    # React crash renders a blank page and the assertion failure says only
    # "element not found", which sends you looking in the wrong place.
    #
    # `pageerror` only — an uncaught exception. Console errors are NOT collected:
    # Chromium logs "Failed to load resource: 401" for the `GET /api/auth/me`
    # that every first visit makes, which is the correct answer to "is anyone
    # signed in", and three tests here force 401s and 500s on purpose. Failing
    # on those would mean asserting that the app never meets an error, when what
    # is being tested is how it behaves when it does.
    errors: list[str] = []
    pg.on("pageerror", lambda e: errors.append(str(e)))

    yield pg

    await ctx.close()
    assert not errors, "the browser threw:\n  " + "\n  ".join(errors)


@pytest_asyncio.fixture
async def phone(browser, app_server):
    """375px wide — E3-S8. iPhone SE, the narrowest width still in real use."""
    ctx = await _context(browser, app_server,
                         viewport={"width": 375, "height": 812},
                         has_touch=True, is_mobile=True)
    pg = await ctx.new_page()
    yield pg
    await ctx.close()


@pytest_asyncio.fixture
async def seeded(app_server, clean_db):
    """The day-one fixture, created through the real endpoints over HTTP.

    Reuses `tests/seed`, so there is one seeder and the browser tests cannot
    drift from the API tests about what "person A" means. `clean_db` truncates
    first, which is what makes A's categories 1-8 (`CV-24`).
    """
    import httpx

    from tests.seed import seed

    async with httpx.AsyncClient(base_url=app_server) as c:
        return await seed(c, guard_database=clean_db)
