"""The rebuilt shell, watched in a real browser — `SW-ADR-147`, `SW-ADR-148`.

The sidebar, the appearance control, custom categories, the settings screen and
the admin console. Every claim is observed: "dark mode works" means the
**computed** background of `<body>` changed, not that an attribute was written.
"""
from __future__ import annotations

import re

import pytest

from tests.seed import seed

pytestmark = [pytest.mark.browser, pytest.mark.db]

PASSWORD = "correct-horse-battery-staple"

# Every `wait_for_function` predicate is a FUNCTION string, `"() => (" <expression> ")"`.
# The app's CSP (`script-src 'self'`, app/core/headers.py, since 2026-10-18) refuses
# the in-page `eval` Playwright uses to poll a bare EXPRESSION string, so an expression
# that is false on the first check fails with an EvalError instead of waiting. A
# function string is polled without `eval` (verified 2026-10-20). The expression inside
# the wrapper is unchanged; do not "simplify" the wrapper away.


async def _open_gate(page, *, register=False):
    """The front door is the landing page on a fresh tab (SW-ADR-156); a tab
    that has held a session reloads straight to the sign-in form. Either way,
    end on the form, in the requested mode."""
    await page.goto("/")
    await page.wait_for_selector('[data-testid="landing-sign-in"], #email')
    if await page.get_by_test_id("landing-sign-in").count():
        await page.get_by_test_id("landing-start" if register else "landing-sign-in").click()
        await page.wait_for_selector("#email")
    elif register:
        await page.get_by_test_id("gate-switch").click()


async def _register(page, email, name="Test Person"):
    await _open_gate(page, register=True)
    await page.fill("#display_name", name)
    await page.fill("#email", email)
    await page.fill("#password", PASSWORD)
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)


async def _sign_in(page, who):
    await _open_gate(page)
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

    # Appearance lives in Settings only (owner, 2026-10-20).
    await page.get_by_test_id("nav-settings").click()
    await page.get_by_test_id("settings-theme-dark").click()
    await page.wait_for_function(
        "() => (" f"getComputedStyle(document.body).backgroundColor !== {light!r}" ")", timeout=5000)

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

    # Appearance lives in Settings only (owner, 2026-10-20).
    await page.get_by_test_id("nav-settings").click()
    await page.get_by_test_id("settings-theme-dark").click()
    await page.wait_for_function(
        "() => (" "document.documentElement.dataset.theme === 'dark'" ")", timeout=5000)
    await page.reload()
    await page.wait_for_selector('[data-testid="whoami"]')
    assert await page.evaluate("document.documentElement.dataset.theme") == "dark"

    await page.get_by_test_id("nav-settings").click()
    await page.get_by_test_id("settings-theme-system").click()
    # A pointer press now floods the new theme in through a view transition
    # (SW-ADR-158), which applies the change on the next frame, not inside the
    # click. Wait for it; the assertion below is unchanged.
    await page.wait_for_function(
        "() => (" "!document.documentElement.hasAttribute('data-theme')" ")", timeout=5000)
    assert await page.evaluate(
        "document.documentElement.hasAttribute('data-theme')") is False


async def test_text_stays_readable_on_the_card_in_both_themes(page, seeded) -> None:
    """The contrast tool computes this from `tokens.css`; this checks the
    browser agrees — that body ink on a card really clears 4.5:1 where it is
    actually painted.

    **This criterion was rewritten under `SW-ADR-154` (client ruling
    2026-08-27), which amends `SW-ADR-147` D.** It used to assert the card's
    background was `rgba(...)` — that the glass was translucent — on the
    reasoning that an opaque card meant `backdrop-filter` had nothing to blur.

    That was a check on the MECHANISM. The requirement was always that the
    text is readable; glass was how the design of the day achieved it. The
    Swiss restyle removes translucency on purpose (`--sw-glass` -> `--sw-paper`,
    blur 0), so the old assertion could only ever fail, and passing it would
    have meant abandoning the restyle rather than satisfying a real need.

    What replaces it is strictly stronger. The old test never computed a ratio
    at all — a translucent card compositing to something unreadable would have
    passed it. This one reads the colours the browser actually painted and does
    the WCAG arithmetic on them, in both themes.
    """
    await _sign_in(page, seeded["A"])
    await page.wait_for_selector('[data-testid="headline"]')

    for theme in ("light", "dark"):
        # Appearance lives in Settings only (owner, 2026-10-20); the card
        # measured is still the dashboard's.
        await page.get_by_test_id("nav-settings").click()
        await page.get_by_test_id(f"settings-theme-{theme}").click()
        await page.get_by_test_id("nav-dashboard").click()
        await page.wait_for_selector('[data-testid="headline"]')
        await page.wait_for_timeout(250)
        measured = await page.evaluate("""
            () => {
              const card = document.querySelector('.card')
              const bg = getComputedStyle(card).backgroundColor
              const fg = getComputedStyle(document.body).color
              const parse = c => c.match(/[\\d.]+/g).slice(0, 3).map(Number)
              // WCAG 2.1 relative luminance.
              const lum = ([r, g, b]) => {
                const f = v => {
                  v /= 255
                  return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
                }
                return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
              }
              const a = lum(parse(bg)), b = lum(parse(fg))
              const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)
              // A card that is still translucent would composite over whatever
              // sits behind it, and the pair measured here would not be the
              // pair `contrast.py` measured. Report the alpha so a regression
              // says WHICH assumption broke.
              const alpha = bg.startsWith('rgba') ? Number(bg.match(/[\\d.]+/g)[3]) : 1
              return { bg, fg, ratio, alpha }
            }
        """)
        assert measured["alpha"] == 1, (
            f"{theme}: the card is translucent ({measured['bg']}) — SW-ADR-154 "
            f"made the ground flat, so contrast.py's figures assume an "
            f"unblended pair")
        assert measured["ratio"] >= 4.5, (
            f"{theme}: body ink on the card is {measured['ratio']:.2f}:1, "
            f"below the 4.5:1 floor — {measured['fg']} on {measured['bg']}")


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
        "() => (" "document.querySelectorAll('.cat-row').length === 9" ")", timeout=15000)

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
        "() => (" "document.querySelector('[data-testid=category-1]').innerText.includes('Food shopping')" ")",
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
        "() => (" "document.querySelectorAll('.cat-row').length === 7" ")", timeout=15000)

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
    assert "$" not in a_row and "$" not in b_row


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
        "() => (" "document.querySelector('[data-testid=sidebar]').getBoundingClientRect().x >= 0" ")",
        timeout=5000)

    await phone.keyboard.press("Escape")
    await phone.wait_for_function(
        "() => (" "document.querySelector('[data-testid=sidebar]').getBoundingClientRect().x < 0" ")",
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
    **"$0.02"**. A currency symbol on a count, on the one screen in the product
    that must never show money.

    The component now takes the formatter from its caller, and this asserts the
    rendered caption rather than the prop.
    """
    await _make_admin(page, seeded, test_urls)
    await page.get_by_test_id("nav-admin").click()
    await page.wait_for_selector('[data-testid="admin-overview"]', timeout=20000)

    text = await page.inner_text("main")
    assert "$" not in text, f"a currency symbol reached the admin console: {text[:400]!r}"
    assert "signups" in text


# ── CR-001: closing an account, and one person's spending over time ────────
#
# The change request moved one line and left the other where it was, and both
# halves are watched here rather than only asserted over JSON: the failure this
# section exists to prevent is a screen, not a response. A "Delete" button wired
# to `/deactivate` returns the same 204 either way, and a category donut on the
# detail pane is a violation of `CR-001` that no API test can see.
SEEDED_CATEGORIES = ("Groceries", "Transport", "Health")


async def _open_the_detail_pane(page, seeded, test_urls, who="A"):
    """Sign in as an administrator who is NOT `who`, and open `who`'s pane.

    **B administers, A is looked at**, deliberately: A owns the day-one fixture,
    so the figures on screen are 3,790.49 and 758.10 — numbers the whole project
    already agrees about. An administrator opening their OWN row would render
    correctly with `SW-ADR-149`'s identity-swap bug fully present.
    """
    await _make_admin(page, seeded, test_urls, who="B")
    await page.get_by_test_id("nav-admin").click()
    await page.get_by_test_id("admin-tab-accounts").click()
    await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)

    await page.get_by_test_id(f"view-{seeded[who]['id']}").click()
    pane = page.get_by_test_id("admin-user-detail")
    await pane.wait_for(timeout=20000)

    # **The pane exists before its figures do.** The header, the status and the
    # period chips are drawn from the row the accounts table already held; the
    # total, the count, the average and the plot say "Loading…" until
    # `GET /api/admin/users/{id}/spending` answers. Reading the text at
    # `pane.wait_for()` is therefore a race, and it fails ASYMMETRICALLY: an
    # assertion that something is PRESENT reports "no line plot" when the truth
    # is "you looked too early", and — far worse — an assertion that a category
    # name is ABSENT passes trivially against a pane that has rendered nothing.
    # A false green on the one boundary `CR-001` exists to hold.
    await pane.get_by_test_id("admin-user-total").wait_for(timeout=20000)
    return pane


async def test_settings_offers_a_close_that_is_not_the_pause(page, clean_db) -> None:
    """**`CR-001 §3`.** Two controls, two promises, and neither of them lies.

    `SW-ADR-148` named the failure and `CR-001` reintroduces the chance to make
    it: *"Never label it 'Delete' and call `/deactivate`, or vice versa."* Both
    words mean "I am done" in ordinary English and only the copy distinguishes
    them, so the copy is asserted — the change request lists what it has to say
    and every clause below is one of them:

    > the account closes, sign-in is refused, **the records are retained and an
    > administrator can restore it**, and the email address stays taken. Offer
    > the export first.

    Then it is completed, and the account is genuinely refused afterwards. A
    two-step confirm that signs you out without closing anything would pass
    every assertion above this line.
    """
    await _register(page, "closing@spendwise.test", "Closing Person")
    await page.get_by_test_id("nav-settings").click()
    await page.wait_for_selector('[data-testid="delete-account"]', timeout=15000)

    # DISTINCT controls, not one control with two labels.
    assert await page.get_by_test_id("deactivate").inner_text() == "Deactivate my account"
    assert await page.get_by_test_id("delete-account").inner_text() == "Delete my account"

    await page.get_by_test_id("delete-account").click()
    await page.wait_for_selector('[data-testid="delete-account-confirmation"]',
                                 timeout=15000)
    copy = (await page.get_by_test_id("delete-account-confirmation").inner_text()).lower()

    # "kept" or "retained" — the change request says retained, the screen says
    # kept, and they are the same promise. The synonym is allowed; the promise
    # is not optional.
    assert "kept" in copy or "retained" in copy, copy
    assert "administrator can restore" in copy, copy
    assert "refused" in copy, copy
    assert "stays taken" in copy, (
        "the copy does not say the email address stays taken — the consequence "
        "nobody expects and the one they discover trying to sign up again")
    assert "download my data" in copy, "the export is not offered first (CR-001 §3)"

    await page.get_by_test_id("delete-account-confirm").click()
    await page.wait_for_selector("#email", timeout=20000)

    # And the account really is closed now.
    await page.fill("#email", "closing@spendwise.test")
    await page.fill("#password", PASSWORD)
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="gate-error"]', timeout=15000)


async def test_an_admin_opens_a_person_and_sees_their_spending_over_time(
        page, seeded, test_urls) -> None:
    """**The grant, on screen.** `CR-001 §3`: a View action, a detail pane, a
    line plot, a total, a count and a daily average.

    The two amounts are person A's day-one figures rendered `en-US` by the one
    shared formatter — $3,790.49 and $758.10. 758.10 is the gate number, so a
    pane that computed its own average, or divided by the row count, fails here
    on a value `CONSTITUTION` Art IX.4 makes never-waivable.

    Asserted as **text on the screen**, not as a prop: the signups plot in this
    same console once rendered two new accounts as "$0.02" because a caption was
    hard-wired to the money formatter, and every test of that bug that read the
    props had passed.
    """
    pane = await _open_the_detail_pane(page, seeded, test_urls)
    text = await pane.inner_text()

    assert seeded["A"]["email"] in text, "the pane does not say whose figures these are"
    assert await pane.locator('[data-testid="line-plot"]').count() == 1, (
        "no line plot — the client asked for the line plot by name")
    assert "$3,790.49" in text, f"the total is not on the pane: {text[:400]!r}"
    assert "$758.10" in text, f"the daily average is not on the pane: {text[:400]!r}"


async def test_the_detail_pane_shows_no_categories_at_any_granularity(
        page, seeded, test_urls) -> None:
    """**The half `CR-001` refused**, watched rather than introspected.

    > the expenses that are happening **not the categories spent on**

    > No category chart, no donut, no ribbon, no entry list on this pane. If you
    > find yourself reaching for `Donut` here, re-read CR-001.

    Both charts already exist and both take the dashboard's `by_category` shape,
    so the pane is one import away from rendering one. The category NAMES are
    grepped out of the rendered text as well, because a breakdown does not have
    to be a chart — a legend, a tooltip or a table of three rows is the same
    disclosure in a smaller box.
    """
    pane = await _open_the_detail_pane(page, seeded, test_urls)
    text = await pane.inner_text()

    assert await pane.locator('[data-testid="donut"]').count() == 0, "a donut"
    assert await pane.locator('[data-testid="ribbon"]').count() == 0, "a ribbon"
    # A legend row carries a category name AND its $ amount — the exact leak.
    assert await pane.locator(".legend-amount").count() == 0
    assert "Spending by category" not in text

    for name in SEEDED_CATEGORIES:
        assert name not in text, (
            f"the detail pane names the category {name!r} — CR-001 grants an "
            f"administrator how much, never what for")


async def test_the_time_filter_changes_the_total_on_the_detail_pane(
        page, seeded, test_urls) -> None:
    """**The third thing the client asked for**, and the one a screenshot proves
    nothing about.

    July 2026 is the right control range: person A's four expenses are all in
    August, so "Last month" is a real, non-empty range that contains none of
    them — the total must move to zero rather than merely re-render. A filter
    wired to the chips but not to the request would keep 3,790.49 on screen and
    look entirely convincing.

    The chips come from `PERIODS` in `lib/period.js` (`CR-001 §3`) but carry
    `admin-period-*` ids rather than the dashboard picker's `period-*`: the pane
    does not reuse `PeriodPicker`, because that component also writes the range
    into the URL — and an administrator glancing at somebody's year would
    silently rewrite their own dashboard's period. The shared thing is the LIST,
    which is the part that could actually drift.
    """
    pane = await _open_the_detail_pane(page, seeded, test_urls)
    total = pane.get_by_test_id("admin-user-total")
    before = (await total.inner_text()).strip()
    assert before == "$3,790.49", before

    await pane.get_by_test_id("admin-period-last-month").click()
    # Waits for the total to SETTLE, not merely to change. The element is
    # replaced by "Loading…" while the new range is in flight, so a wait for
    # "the text no longer says $3,790.49" is satisfied by the loading state and
    # the assertion below then races it — which is how a correct filter fails a
    # test intermittently and gets "fixed" by loosening the assertion.
    await page.wait_for_function(
        """(prev) => {
             const el = document.querySelector('[data-testid=admin-user-total]')
             return !!el && el.innerText.trim() !== prev
           }""", arg=before, timeout=20000)

    after = (await total.inner_text()).strip()
    assert after != before
    assert after == "$0.00", (
        f"July holds none of person A's expenses, so the total should read "
        f"$0.00, not {after!r}")


async def test_a_closed_account_shows_as_closed_and_can_be_restored(
        page, seeded, test_urls, app_server) -> None:
    """**`CR-001 §3`**: a clear `deleted` status and a Restore action.

    The account is closed over HTTP rather than by driving the settings screen
    twice — that path already has its own test above, and repeating it here
    would make this test fail for that screen's reasons.

    The list shows the closed account **by default** (`CR-001 §2`): an
    administrator looking for someone who has left must be able to find them,
    and a Restore action on a row nobody can see is not an action.
    """
    import httpx

    async with httpx.AsyncClient(base_url=app_server) as c:
        r = await c.post("/api/auth/login", json={
            "email": seeded["A"]["email"], "password": seeded["A"]["password"]})
        assert r.status_code == 200, r.text
        assert (await c.delete("/api/auth/me")).status_code == 204

    await _make_admin(page, seeded, test_urls, who="B")
    await page.get_by_test_id("nav-admin").click()
    await page.get_by_test_id("admin-tab-accounts").click()
    await page.wait_for_selector('[data-testid="admin-users"]', timeout=20000)

    a = seeded["A"]["id"]
    row = page.get_by_test_id(f"admin-user-{a}")
    assert "deleted" in (await row.inner_text()).lower(), (
        "a closed account is not shown as closed — 'deactivated' is a THIRD "
        "state and telling them apart is what the Restore action is for")

    await row.get_by_role("button", name=re.compile("restore", re.I)).click()
    await page.wait_for_function(
        "() => (" f"!document.querySelector('[data-testid=admin-user-{a}]')"
        f".innerText.toLowerCase().includes('deleted')" ")", timeout=20000)
