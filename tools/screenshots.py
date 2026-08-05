#!/usr/bin/env python3
"""Photograph the running website. Evidence, not decoration.

Starts the real server against `spendwise_test`, seeds the day-one fixture
through the real endpoints, and photographs six screens — including the one
with 758.10 on it.

    py tools/screenshots.py

Writes into `evidence/screens/`. Uses the TEST database and
`APP_TODAY_OVERRIDE=2026-08-05`, the same pinning `SW-ADR-146` made explicit,
so the pictures are reproducible rather than a record of the day they were
taken.
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "evidence" / "screens"
GATE_DAY = "2026-08-05"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _swap_db(url: str) -> str:
    import re
    return re.sub(r"/(?:spendwise)(\?|$)", r"/spendwise_test\1", url, count=1)


async def main() -> int:
    from app.core.settings import get_settings
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    s = get_settings()
    runtime = _swap_db(s.DATABASE_URL.get_secret_value())
    owner = _swap_db(s.MIGRATION_DATABASE_URL.get_secret_value())

    # A clean start, as the owner — the runtime role holds no DELETE on users
    # and `verify_invariants.sql` asserts it cannot (`SW-ADR-137`).
    engine = create_async_engine(owner, poolclass=None)
    async with engine.begin() as c:
        await c.execute(text(
            "TRUNCATE expenses, categories, sessions, password_resets, "
            "admin_audit_log, users, app_meta RESTART IDENTITY CASCADE"))
    await engine.dispose()

    port = _free_port()
    env = {**os.environ, "DATABASE_URL": runtime, "MIGRATION_DATABASE_URL": owner,
           "JWT_SECRET": s.JWT_SECRET.get_secret_value(), "SPENDWISE_DOTENV": "0",
           "APP_TODAY_OVERRIDE": GATE_DAY, "COOKIE_SECURE": "false",
           "EXPOSE_VERSION": "screenshots", "LOG_LEVEL": "INFO"}

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    base = f"http://127.0.0.1:{port}"
    try:
        import urllib.request
        for _ in range(120):
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

        from tests.seed import seed
        async with httpx.AsyncClient(base_url=base) as c:
            made = await seed(c, guard_database=runtime)

        OUT.mkdir(parents=True, exist_ok=True)
        from playwright.async_api import async_playwright

        shots = 0
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            async def shot(page, name, full=True):
                nonlocal shots
                await page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
                shots += 1
                print(f"  {name}.png")

            async def sign_in(page, who):
                await page.goto("/")
                await page.wait_for_selector("#email")
                await page.fill("#email", who["email"])
                await page.fill("#password", who["password"])
                await page.get_by_test_id("gate-submit").click()
                await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)

            async def new_page(**kw):
                ctx = await browser.new_context(
                    base_url=base, locale="en-IN", timezone_id="Asia/Kolkata", **kw)
                await ctx.add_init_script(f"window.__SPENDWISE_TODAY__ = '{GATE_DAY}';")
                return ctx, await ctx.new_page()

            desktop = {"viewport": {"width": 1280, "height": 900},
                       "device_scale_factor": 2}

            ctx, page = await new_page(**desktop)
            await page.goto("/")
            await page.wait_for_selector("#email")
            await shot(page, "01-sign-in", full=False)
            await ctx.close()

            ctx, page = await new_page(**desktop)
            await sign_in(page, made["A"])
            await page.wait_for_selector('[data-testid="daily-average"]')
            await shot(page, "02-dashboard-person-a")

            await page.locator(".band").first.click()
            await page.wait_for_selector('.ribbon[data-filtering="true"]')
            await page.wait_for_timeout(600)
            await shot(page, "03-filtered-by-category")

            await page.keyboard.press("Escape")
            await page.wait_for_timeout(400)
            await page.get_by_test_id("add-expense").click()
            await page.wait_for_selector('[data-testid="expense-panel"]')
            await page.fill("input[name='amount']", "845.50")
            await page.fill("input[name='description']", "Dinner")
            await page.wait_for_timeout(300)
            await shot(page, "04-add-expense-panel", full=False)
            await ctx.close()

            ctx, page = await new_page(**desktop)
            await sign_in(page, made["B"])
            await page.wait_for_selector('[data-testid="total"]')
            await shot(page, "05-person-b-sees-only-their-own")
            await ctx.close()

            ctx, page = await new_page(**desktop)
            await sign_in(page, made["A"])
            await page.wait_for_selector('[data-testid="daily-average"]')
            await page.get_by_test_id("theme-dark").click()
            await page.wait_for_timeout(500)
            await shot(page, "06-dashboard-dark")

            await page.get_by_test_id("nav-categories").click()
            await page.wait_for_selector('[data-testid="category-list"]')
            await shot(page, "07-categories-dark")

            await page.get_by_test_id("theme-light").click()
            await page.wait_for_timeout(400)
            await page.get_by_test_id("nav-settings").click()
            await page.wait_for_selector('[data-testid="deactivate"]')
            await shot(page, "08-settings")
            await ctx.close()

            # The administrator. Promoted through the owner connection, because
            # promoting requires an admin and this is the first one.
            from sqlalchemy import text as _text
            from sqlalchemy.ext.asyncio import create_async_engine as _engine
            eng = _engine(owner, poolclass=None)
            async with eng.begin() as c:
                await c.execute(_text("UPDATE users SET role='admin' WHERE id=:i"),
                                {"i": made["A"]["id"]})
            await eng.dispose()

            ctx, page = await new_page(**desktop)
            await sign_in(page, made["A"])
            await page.get_by_test_id("nav-admin").click()
            await page.wait_for_selector('[data-testid="admin-overview"]', timeout=20000)
            await shot(page, "09-admin-overview")

            await page.get_by_test_id("admin-tab-accounts").click()
            await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)
            await shot(page, "10-admin-accounts")
            await ctx.close()

            ctx, page = await new_page(viewport={"width": 375, "height": 812},
                                       device_scale_factor=2,
                                       has_touch=True, is_mobile=True)
            await sign_in(page, made["A"])
            await page.wait_for_selector('[data-testid="daily-average"]')
            await shot(page, "11-phone-375px")
            await ctx.close()

            await browser.close()

        print(f"\n  {shots} screens -> {OUT.relative_to(ROOT)}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
