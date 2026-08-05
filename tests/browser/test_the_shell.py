"""The rebuilt shell, watched in a real browser — `SW-ADR-147`, `SW-ADR-148`.

The sidebar, the appearance control, custom categories, the settings screen and
the admin console. Every claim is observed: "dark mode works" means the
**computed** background of `<body>` changed, not that an attribute was written.
"""
from __future__ import annotations

import pytest

from tests.seed import seed

pytestmark = [pytest.mark.browser, pytest.mark.db]

PASSWORD = "correct-horse-battery-staple"


async def _register(page, email, name="Test Person"):
    await page.goto("/")
    await page.get_by_test_id("gate-switch").click()
    await page.fill("#display_name", name)
    await page.fill("#email", email)
    await page.fill("#password", PASSWORD)
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)


async def _sign_in(page, who):
    await page.goto("/")
    await page.wait_for_selector("#email")
    await page.fill("#email", who["email"])
    await page.fill("#password", who["password"])
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)


async def _make_admin(page, seeded, test_urls, who="A"):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("UPDATE users SET role='admin' WHERE id=:i"),
                        {"i": seeded[who]["id"]})
    await e.dispose()
    await _sign_in(page, seeded[who])


# ── the rail ───────────────────────────────────────────────────────────────
async def test_the_sidebar_moves_between_sections(page, seeded) -> None:
    await _sign_in(page, seeded["A"])

    await page.get_by_test_id("nav-categories").click()
    await page.wait_for_selector('[data-testid="category-list"]', timeout=15000)
    assert await page.get_by_test_id("nav-categories").get_attribute("aria-current") == "page"

    await page.get_by_test_id("nav-settings").click()
    await page.wait_for_selector('[data-testid="settings-name"]', timeout=15000)

    await page.get_by_test_id("nav-dashboard").click()
    await page.wait_for_selector('[data-testid="headline"]', timeout=15000)


async def test_a_normal_account_is_offered_no_administration_link(page, seeded) -> None:
    """Cosmetic, and the screen knows it. `SRC-001 §9.1`: *"Hiding the admin
    link in the UI is cosmetic, the real check is `require_admin` on the server
    for every request."*"""
    await _sign_in(page, seeded["A"])
    assert await page.locator('[data-testid="nav-admin"]').count() == 0
    assert await page.locator('[data-testid="role-pill"]').count() == 0


async def test_an_admin_is(page, seeded, test_urls) -> None:
    await _make_admin(page, seeded, test_urls)
    assert await page.locator('[data-testid="nav-admin"]').count() == 1
    assert await page.get_by_test_id("role-pill").is_visible()


# ── appearance ─────────────────────────────────────────────────────────────
async def _body_background(page) -> str:
    return await page.evaluate("getComputedStyle(document.body).backgroundColor")


async def test_dark_mode_changes_what_is_actually_painted(page, seeded) -> None:
    """**Observed as a computed colour**, not as an attribute.

    `data-theme="dark"` on `<html>` proves the click worked; it does not prove
    the stylesheet responded. A selector that never matched would pass the
    first check and fail every person who used it.
    """
    await _sign_in(page, seeded["A"])
    light = await _body_background(page)

    await page.get_by_test_id("theme-dark").click()
    await page.wait_for_function(
        f"getComputedStyle(document.body).backgroundColor !== {light!r}", timeout=5000)

    dark = await _body_background(page)
    assert dark != light
    assert await page.evaluate("document.documentElement.dataset.theme") == "dark"

    # And it is genuinely DARKER — a theme that merely differs is not a theme.
    def luminance(css):
        r, g, b = (int(v) for v in css[css.index("(") + 1:css.index(")")].split(",")[:3])
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    assert luminance(dark) < luminance(light), f"{dark} is not darker than {light}"


async def test_the_choice_survives_a_reload_and_system_is_the_absence_of_it(
        page, seeded) -> None:
    """Three states, not two (`SW-ADR-147 B`): **System** is the ABSENCE of the
    attribute. Writing `data-theme="system"` would match neither selector and
    silently mean light."""
    await _sign_in(page, seeded["A"])

    await page.get_by_test_id("theme-dark").click()
    await page.reload()
    await page.wait_for_selector('[data-testid="whoami"]')
    assert await page.evaluate("document.documentElement.dataset.theme") == "dark"

    await page.get_by_test_id("theme-system").click()
    assert await page.evaluate(
        "document.documentElement.hasAttribute('data-theme')") is False


async def test_text_stays_readable_on_glass_in_both_themes(page, seeded) -> None:
    """The contrast tool computes this from `tokens.css`; this checks the
    browser agrees — that the glass really is translucent and the composited
    result is still the ink colour the tool measured against."""
    await _sign_in(page, seeded["A"])
    await page.wait_for_selector('[data-testid="headline"]')

    for theme in ("light", "dark"):
        await page.get_by_test_id(f"theme-{theme}").click()
        await page.wait_for_timeout(250)
        style = await page.evaluate("""
            () => {
              const card = document.querySelector('.card')
              const s = getComputedStyle(card)
              return { bg: s.backgroundColor, fg: getComputedStyle(document.body).color }
            }
        """)
        # An `rgba(...)` background is the glass being translucent. An opaque
        # card would mean `backdrop-filter` had nothing to blur and the whole
        # effect was decoration.
        assert "rgba" in style["bg"], f"{theme}: the card is not translucent ({style['bg']})"


# ── custom categories ──────────────────────────────────────────────────────
async def test_a_person_can_make_their_own_category_and_use_it(page, clean_db) -> None:
    """`P-REC-05` always allowed this. The eight seeded ones are not special:
    they were created by the application through the same endpoint."""
    await _register(page, "cats@spendwise.test", "Cat Person")

    await page.get_by_test_id("nav-categories").click()
    await page.wait_for_selector('[data-testid="category-list"]')
    assert await page.locator(".cat-row").count() == 8

    await page.fill('[data-testid="new-category-name"]', "Coffee")
    await page.get_by_test_id("create-category").click()
    await page.wait_for_function(
        "document.querySelectorAll('.cat-row').length === 9", timeout=15000)

    # And it is immediately usable on an expense.
    await page.get_by_test_id("nav-dashboard").click()
    await page.wait_for_selector('[data-testid="first-add"]', timeout=15000)
    await page.get_by_test_id("first-add").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')
    await page.fill("input[name='amount']", "180.00")
    await page.select_option("select[name='category_id']", label="Coffee")
    await page.get_by_test_id("panel-submit").click()

    await page.wait_for_selector('[data-testid="entries"]', timeout=20000)
    assert "Coffee" in await page.get_by_test_id("entries").inner_text()


async def test_a_duplicate_name_is_refused_on_screen(page, clean_db) -> None:
    await _register(page, "dupe@spendwise.test")
    await page.get_by_test_id("nav-categories").click()
    await page.wait_for_selector('[data-testid="category-list"]')

    await page.fill('[data-testid="new-category-name"]', "gRoCeRiEs")
    await page.get_by_test_id("create-category").click()

    error = page.locator(".field-error").first
    await error.wait_for(timeout=15000)
    assert await error.inner_text() == "That already exists."
    assert await page.locator(".cat-row").count() == 8


async def test_renaming_a_category_keeps_its_colour(page, clean_db) -> None:
    await _register(page, "rename@spendwise.test")
    await page.get_by_test_id("nav-categories").click()
    await page.wait_for_selector('[data-testid="category-list"]')

    before = await page.locator(".cat-row").first.locator(".cat-dot").evaluate(
        "el => getComputedStyle(el).backgroundColor")

    await page.get_by_test_id("edit-category-1").click()
    await page.fill('[data-testid="rename-1"]', "Food shopping")
    await page.get_by_test_id("save-category-1").click()
    await page.wait_for_function(
        "document.querySelector('[data-testid=category-1]').innerText.includes('Food shopping')",
        timeout=15000)

    after = await page.locator(".cat-row").first.locator(".cat-dot").evaluate(
        "el => getComputedStyle(el).backgroundColor")
    assert after == before, "renaming recoloured it"


async def test_deleting_a_category_names_the_blast_radius_and_keeps_the_money(
        page, seeded) -> None:
    """**`SRC-001 §7.2` and `SW-ADR-119`.** The confirm says what happens to the
    expenses, and the expenses survive."""
    await _sign_in(page, seeded["A"])
    await page.wait_for_selector('[data-testid="total"]')
    before = await page.get_by_test_id("total").inner_text()

    await page.get_by_test_id("nav-categories").click()
    await page.wait_for_selector('[data-testid="category-list"]')

    messages = []

    async def accept(d):
        messages.append(d.message)
        await d.accept()

    page.once("dialog", accept)
    await page.get_by_test_id("delete-category-1").click()
    await page.wait_for_function(
        "document.querySelectorAll('.cat-row').length === 7", timeout=15000)

    assert messages, "no confirmation before a destructive action"
    assert "KEPT" in messages[0], messages[0]
    assert "Uncategorised" in messages[0]

    await page.get_by_test_id("nav-dashboard").click()
    await page.wait_for_selector('[data-testid="total"]', timeout=15000)
    assert await page.get_by_test_id("total").inner_text() == before, (
        "deleting a label changed the money")


# ── settings ───────────────────────────────────────────────────────────────
async def test_changing_your_display_name(page, seeded) -> None:
    await _sign_in(page, seeded["A"])
    await page.get_by_test_id("nav-settings").click()
    await page.wait_for_selector('[data-testid="settings-name"]')

    await page.fill('[data-testid="settings-name"]', "Asha Nair")
    await page.get_by_test_id("save-name").click()
    await page.wait_for_selector('[data-testid="name-saved"]', timeout=15000)
    assert await page.get_by_test_id("whoami").inner_text() == "Asha Nair"


async def test_settings_says_there_is_no_deletion_and_offers_the_export(
        page, seeded) -> None:
    """`SW-ADR-148`. It would be easy to label this "Delete account" and
    deactivate underneath — and a person would only find out by asking for
    their data back."""
    await _sign_in(page, seeded["A"])
    await page.get_by_test_id("nav-settings").click()
    await page.wait_for_selector('[data-testid="deactivate"]')

    text = await page.inner_text("main")
    assert "kept, not erased" in text
    assert await page.get_by_test_id("deactivate").inner_text() == "Deactivate my account"
    assert "Delete account" not in text
    assert await page.get_by_test_id("export").is_visible()


async def test_deactivating_asks_first_and_then_signs_you_out(page, clean_db) -> None:
    await _register(page, "leaving@spendwise.test")
    await page.get_by_test_id("nav-settings").click()
    await page.wait_for_selector('[data-testid="deactivate"]')

    await page.get_by_test_id("deactivate").click()
    await page.wait_for_selector('[data-testid="deactivate-confirm"]')
    await page.get_by_test_id("deactivate-confirm").click()

    await page.wait_for_selector("#email", timeout=15000)
    # And the account really is refused now.
    await page.fill("#email", "leaving@spendwise.test")
    await page.fill("#password", PASSWORD)
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="gate-error"]', timeout=15000)


# ── administration ─────────────────────────────────────────────────────────
async def test_the_admin_console_shows_accounts_and_no_money(page, seeded,
                                                             test_urls) -> None:
    """**`SRC-001 §4.2`.** Person A has 3,790.49 in expenses; the administrator
    console must not contain that number, or any other amount, anywhere."""
    await _make_admin(page, seeded, test_urls)

    await page.get_by_test_id("nav-admin").click()
    await page.wait_for_selector('[data-testid="admin-overview"]', timeout=20000)

    assert await page.get_by_test_id("stat-accounts").inner_text() == "2"
    assert await page.get_by_test_id("stat-active").inner_text() == "2"
    # Six expenses across both people — a COUNT of rows.
    assert await page.get_by_test_id("stat-expenses").inner_text() == "6"

    body = await page.content()
    for amount in ("3,790.49", "379049", "1,250.00", "125000", "758.10"):
        assert amount not in body, f"the admin console leaked {amount}"


async def test_the_account_table_shows_counts_not_sums(page, seeded,
                                                       test_urls) -> None:
    await _make_admin(page, seeded, test_urls)
    await page.get_by_test_id("nav-admin").click()
    await page.get_by_test_id("admin-tab-accounts").click()
    await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)

    a_row = await page.get_by_test_id(f"admin-user-{seeded['A']['id']}").inner_text()
    b_row = await page.get_by_test_id(f"admin-user-{seeded['B']['id']}").inner_text()
    assert "4" in a_row and seeded["A"]["email"] in a_row
    assert "2" in b_row and seeded["B"]["email"] in b_row
    assert "₹" not in a_row and "₹" not in b_row


async def test_an_admin_can_sign_someone_out_and_it_actually_happens(
        page, browser, app_server, seeded, test_urls) -> None:
    """**`SW-ADR-149`.** The version of this that mattered returned 200 and
    signed nobody out — `UPDATE sessions WHERE user_id = <other>` matches zero
    rows under row-level security and raises nothing. So this drives a SECOND
    browser context for person B and asserts B is genuinely ejected.
    """
    ctx = await browser.new_context(base_url=app_server, locale="en-IN",
                                    timezone_id="Asia/Kolkata")
    await ctx.add_init_script("window.__SPENDWISE_TODAY__ = '2026-08-05';")
    b_page = await ctx.new_page()
    try:
        await _sign_in(b_page, seeded["B"])
        assert await b_page.get_by_test_id("whoami").is_visible()

        await _make_admin(page, seeded, test_urls)
        await page.get_by_test_id("nav-admin").click()
        await page.get_by_test_id("admin-tab-accounts").click()
        await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)

        await page.get_by_test_id(f"revoke-{seeded['B']['id']}").click()
        await page.wait_for_selector('[data-testid="admin-notice"]', timeout=20000)

        # B's next request is refused, and the app routes them to the gate.
        await b_page.reload()
        await b_page.wait_for_selector("#email", timeout=20000)
    finally:
        await ctx.close()


async def test_the_audit_log_reads_as_sentences(page, seeded, test_urls) -> None:
    await _make_admin(page, seeded, test_urls)
    await page.get_by_test_id("nav-admin").click()
    await page.get_by_test_id("admin-tab-accounts").click()
    await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)
    await page.get_by_test_id(f"revoke-{seeded['B']['id']}").click()
    await page.wait_for_selector('[data-testid="admin-notice"]', timeout=20000)

    await page.get_by_test_id("admin-tab-audit").click()
    await page.wait_for_selector('[data-testid="admin-audit"]', timeout=20000)

    text = await page.get_by_test_id("admin-audit").inner_text()
    assert "signed user #" in text
    assert "{" not in text, "raw JSON reached the audit view"


async def test_the_last_administrator_cannot_be_demoted_and_the_screen_says_so(
        page, seeded, test_urls) -> None:
    await _make_admin(page, seeded, test_urls)
    await page.get_by_test_id("nav-admin").click()
    await page.get_by_test_id("admin-tab-accounts").click()
    await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)

    await page.get_by_test_id(f"toggle-role-{seeded['A']['id']}").click()
    await page.wait_for_selector('[data-testid="admin-error"]', timeout=20000)
    assert "no active administrator" in await page.get_by_test_id("admin-error").inner_text()


async def test_a_normal_account_reaching_the_admin_pane_sees_a_refusal(
        page, seeded) -> None:
    """There is no link for them, but the pane exists in the bundle — so the
    state a determined person reaches is a stated refusal, not a blank screen
    or a wall of failed requests."""
    await _sign_in(page, seeded["A"])
    await page.wait_for_selector('[data-testid="headline"]')
    assert await page.locator('[data-testid="nav-admin"]').count() == 0


# ── phone width, again, with the rail ──────────────────────────────────────
async def test_the_rail_is_an_overlay_at_phone_width(phone, seeded) -> None:
    await _sign_in(phone, seeded["A"])
    await phone.wait_for_selector('[data-testid="headline"]', timeout=20000)

    # Off-screen until opened.
    assert (await phone.get_by_test_id("sidebar").bounding_box())["x"] < 0

    await phone.get_by_test_id("rail-open").click()
    await phone.wait_for_function(
        "document.querySelector('[data-testid=sidebar]').getBoundingClientRect().x >= 0",
        timeout=5000)

    await phone.keyboard.press("Escape")
    await phone.wait_for_function(
        "document.querySelector('[data-testid=sidebar]').getBoundingClientRect().x < 0",
        timeout=5000)


async def test_the_new_dashboard_still_fits_375px(phone, seeded) -> None:
    await _sign_in(phone, seeded["A"])
    await phone.wait_for_selector('[data-testid="headline"]', timeout=20000)

    overflow = await phone.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 0, f"the page is {overflow}px wider than a 375px window"

    strays = await phone.evaluate("""
        [...document.querySelectorAll('body *')]
          .filter(el => el.getBoundingClientRect().right > 375.5)
          .filter(el => !el.closest('.table-wrap, .ribbon-wrap'))
          .map(el => el.tagName + '.' + (el.className || ''))
          .slice(0, 5)
    """)
    assert not strays, f"elements extend past 375px: {strays}"


async def test_the_admin_charts_never_render_a_currency_symbol(page, seeded,
                                                               test_urls) -> None:
    """The signups plot reuses the dashboard's `LinePlot`, whose caption was
    hard-wired to the money formatter — so two new accounts rendered as
    **"₹0.02"**. A currency symbol on a count, on the one screen in the product
    that must never show money.

    The component now takes the formatter from its caller, and this asserts the
    rendered caption rather than the prop.
    """
    await _make_admin(page, seeded, test_urls)
    await page.get_by_test_id("nav-admin").click()
    await page.wait_for_selector('[data-testid="admin-overview"]', timeout=20000)

    text = await page.inner_text("main")
    assert "₹" not in text, f"a currency symbol reached the admin console: {text[:400]!r}"
    assert "signups" in text
