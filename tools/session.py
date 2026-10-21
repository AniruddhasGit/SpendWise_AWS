#!/usr/bin/env python3
"""A hands-on session against the DEV database, driven and photographed.

Not a test suite — the suite already ran. This is the thing you do before
handing something over: sign in as a real person, click the new controls, and
look at what comes back.

    py tools/session.py

Runs against `spendwise` with the two accounts `reset_and_seed.py` made, so
what it photographs is what the client sees at `localhost:8000`.

**It does not touch either of those two accounts destructively.** The
delete-and-restore loop runs against a scratch account it registers itself,
because proving that closing an account works by closing the account somebody
signs in with would be a poor trade.
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

OUT = ROOT / "evidence" / "session"


def _account(env_var: str, email: str) -> tuple[str, str]:
    """An (email, password) pair whose password comes from the environment.

    Passwords are NEVER hard-coded here (F-S4): this file is committed, so a
    literal is a published credential. `reset_and_seed.py` prints the two it
    generates; export them before running:

        export SESSION_ADMIN_PW=...  SESSION_PERSON_PW=...

    The scratch account is registered by this script, so its password is a
    throwaway generated at runtime, never stored.
    """
    pw = os.environ.get(env_var)
    if not pw:
        sys.exit(f"set {env_var} to the {email} password (see reset_and_seed.py output)")
    return (email, pw)


ADMIN = _account("SESSION_ADMIN_PW", "admin@spendwise.app")
PERSON = _account("SESSION_PERSON_PW", "you@spendwise.app")
SCRATCH = ("scratch-leaver@spendwise.app", secrets.token_urlsafe(18))

log: list[str] = []


def note(ok: bool, what: str) -> None:
    """Record and print one observation.

    Anything a Windows console at cp1252 cannot encode is replaced ON THE WAY
    TO THE CONSOLE only (it raises rather than degrading, which once killed a
    passing session at the first rupee sign). The dollar sign (`SW-ADR-157`)
    is ASCII, so this now only guards names and notes. The LOG keeps the real
    string, because the terminal's limitation is not the product's.
    """
    log.append(f"  {'PASS' if ok else 'FAIL'}  {what}")
    print(log[-1].encode("ascii", "replace").decode("ascii"))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def main() -> int:
    from app.core.settings import get_settings

    s = get_settings()
    port = _free_port()
    env = {**os.environ,
           "DATABASE_URL": s.DATABASE_URL.get_secret_value(),
           "MIGRATION_DATABASE_URL": s.MIGRATION_DATABASE_URL.get_secret_value(),
           "JWT_SECRET": s.JWT_SECRET.get_secret_value(),
           "SPENDWISE_DOTENV": "0", "COOKIE_SECURE": "false",
           "EXPOSE_VERSION": "session", "LOG_LEVEL": "WARNING"}

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

        OUT.mkdir(parents=True, exist_ok=True)
        from playwright.async_api import async_playwright

        shots = 0
        async with async_playwright() as p:
            browser = await p.chromium.launch()

            async def new_page(**kw):
                ctx = await browser.new_context(
                    base_url=base, locale="en-IN", timezone_id="Asia/Kolkata",
                    viewport={"width": 1280, "height": 900},
                    device_scale_factor=2, **kw)
                return ctx, await ctx.new_page()

            async def shot(page, name, full=True):
                nonlocal shots
                await page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
                shots += 1

            async def sign_in(page, who):
                await page.goto("/")
                await page.wait_for_selector("#email")
                await page.fill("#email", who[0])
                await page.fill("#password", who[1])
                await page.get_by_test_id("gate-submit").click()
                await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)

            # ── 1. the person's own dashboard ──────────────────────────────
            ctx, page = await new_page()
            await sign_in(page, PERSON)
            await page.wait_for_selector('[data-testid="total"]', timeout=20000)
            total = await page.get_by_test_id("total").inner_text()
            note(total.startswith("$") and total != "$0.00",
                 f"person signs in and sees a real total: {total}")
            await shot(page, "01-person-dashboard")

            # The person must NOT be offered administration.
            note(await page.locator('[data-testid="nav-admin"]').count() == 0,
                 "a normal account is offered no administration link")

            # ── 2. a scratch account closes itself ─────────────────────────
            await page.goto("/")
            await page.get_by_test_id("sign-out").click()
            await page.wait_for_selector("#email")
            await page.get_by_test_id("gate-switch").click()
            await page.fill("#display_name", "Scratch Leaver")
            await page.fill("#email", SCRATCH[0])
            await page.fill("#password", SCRATCH[1])
            await page.get_by_test_id("gate-submit").click()
            await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)

            await page.get_by_test_id("nav-settings").click()
            await page.wait_for_selector('[data-testid="delete-account"]', timeout=15000)
            await shot(page, "02-settings-two-ways-out")

            await page.get_by_test_id("delete-account").click()
            await page.wait_for_selector('[data-testid="delete-account-confirm"]',
                                         timeout=10000)
            confirm_text = await page.inner_text("main")
            note("restore" in confirm_text.lower() and "kept" in confirm_text.lower(),
                 "the close-account confirm says the records are kept and restorable")
            await shot(page, "03-close-account-confirm", full=False)

            await page.get_by_test_id("delete-account-confirm").click()
            await page.wait_for_selector("#email", timeout=15000)
            note(True, "closing the account signed it out")

            await page.fill("#email", SCRATCH[0])
            await page.fill("#password", SCRATCH[1])
            await page.get_by_test_id("gate-submit").click()
            await page.wait_for_selector('[data-testid="gate-error"]', timeout=15000)
            note(True, "a closed account cannot sign back in")
            await ctx.close()

            # ── 3. the administrator ───────────────────────────────────────
            ctx, page = await new_page()
            await sign_in(page, ADMIN)
            await page.get_by_test_id("nav-admin").click()
            await page.wait_for_selector('[data-testid="admin-overview"]', timeout=25000)
            overview = await page.inner_text("main")
            note("$" not in overview, "the admin overview shows no money at all")
            note("closed" in overview, "the overview separates paused from closed")
            await shot(page, "04-admin-overview")

            await page.get_by_test_id("admin-tab-accounts").click()
            await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)
            table = await page.inner_text('[data-testid="admin-users"]')
            note("$" not in table, "the accounts table shows counts, never amounts")
            note("scratch-leaver" in table, "the closed account is still findable")
            await shot(page, "05-admin-accounts")

            # Search, by email.
            await page.fill('[data-testid="admin-search"]', "you@")
            await page.wait_for_timeout(1200)
            found = await page.inner_text('[data-testid="admin-users"]')
            note("you@spendwise.app" in found and "admin@spendwise.app" not in found,
                 "search by email narrows the list")
            await page.fill('[data-testid="admin-search"]', "")
            await page.wait_for_timeout(1200)

            # ── 4. one person's spending, and the time filter ──────────────
            rows = await page.locator('[data-testid^="admin-user-"]').all()
            target = None
            for r in rows:
                if "you@spendwise.app" in await r.inner_text():
                    target = (await r.get_attribute("data-testid")).split("-")[-1]
            note(target is not None, f"found the person's row (id {target})")

            await page.get_by_test_id(f"view-{target}").click()
            await page.wait_for_selector('[data-testid="admin-user-total"]', timeout=25000)
            await page.wait_for_timeout(600)

            spend_total = await page.get_by_test_id("admin-user-total").inner_text()
            spend_avg = await page.get_by_test_id("admin-user-average").inner_text()
            note(spend_total.startswith("$") and spend_total != "$0.00",
                 f"the admin sees the person's total: {spend_total}")
            note(spend_avg.startswith("$"), f"and their daily average: {spend_avg}")

            pane = await page.inner_text('[data-testid="admin-user-detail"]')
            leaked = [c for c in ("Groceries", "Transport", "Health", "Rent",
                                  "Entertainment", "Shopping")
                      if c in pane]
            note(not leaked, f"NO category names on the pane{'' if not leaked else f' — LEAKED {leaked}'}")
            note("line-plot" in await page.inner_html('[data-testid="admin-user-detail"]')
                 or await page.locator('[data-testid="line-plot"]').count() > 0,
                 "the line plot is rendered")
            await shot(page, "06-admin-user-spending")

            # The time filter.
            await page.get_by_test_id("admin-period-last-90").click()
            await page.wait_for_function(
                "el => document.querySelector('[data-testid=admin-user-total]')"
                "?.innerText !== el", arg=spend_total, timeout=20000)
            wider = await page.get_by_test_id("admin-user-total").inner_text()
            note(wider != spend_total,
                 f"the time filter moves the number: {spend_total} -> {wider} (last 90 days)")
            await shot(page, "07-admin-time-filter")

            # ── 5. restore the scratch account ─────────────────────────────
            await page.get_by_test_id("admin-user-back").click()
            await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)
            await page.fill('[data-testid="admin-search"]', "scratch-leaver")
            await page.wait_for_timeout(1500)
            rows = await page.locator('[data-testid^="admin-user-"]').all()
            scratch_id = (await rows[0].get_attribute("data-testid")).split("-")[-1]
            row_text = await rows[0].inner_text()
            note("deleted" in row_text.lower(), "the closed account reads as deleted")

            await page.get_by_test_id(f"toggle-active-{scratch_id}").click()
            await page.wait_for_selector('[data-testid="admin-notice"]', timeout=20000)
            await page.wait_for_timeout(1200)
            restored = await page.inner_text('[data-testid="admin-users"]')
            note("deleted" not in restored.lower(), "restoring cleared the closed state")
            await shot(page, "08-admin-restored")
            await ctx.close()

            # ── 6. the restored account can sign in again ──────────────────
            ctx, page = await new_page()
            await page.goto("/")
            await page.wait_for_selector("#email")
            await page.fill("#email", SCRATCH[0])
            await page.fill("#password", SCRATCH[1])
            await page.get_by_test_id("gate-submit").click()
            try:
                await page.wait_for_selector('[data-testid="whoami"]', timeout=15000)
                note(True, "the restored account signs in again")
            except Exception:                              # noqa: BLE001
                note(False, "the restored account could NOT sign in")
            await ctx.close()

            await browser.close()

        print(f"\n  {shots} screens -> {OUT.relative_to(ROOT)}")
        failed = [l for l in log if l.strip().startswith("FAIL")]
        print(f"  {len(log) - len(failed)}/{len(log)} checks passed")
        return 1 if failed else 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
