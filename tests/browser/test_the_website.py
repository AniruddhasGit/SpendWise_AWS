"""GOAL_14 step 4 — the runs that matter, watched in a real browser.

`CONSTITUTION` Art IX.4 requires the day-one proof observed in a browser, and
these are the six the goal names:

  a. register -> land on the dashboard -> the cookie is httpOnly in the
     browser's OWN store
  b. add an expense through the form -> it appears without a reload
  c. THE GATE ON SCREEN: seeded person A, 2026-08-05, and 758.10 visible
  d. person B signs in and sees their own much smaller number
  e. the ribbon works by keyboard alone
  f. 375px wide, nothing overflows

Every claim here is OBSERVED. "The cookie is httpOnly" means read out of
Chromium's cookie store, not out of the code that sets it. "Nothing overflows"
means `scrollWidth - clientWidth`, which is the browser reporting geometry, not
a stylesheet that was written and might not have applied.
"""
from __future__ import annotations

import re

import pytest

pytestmark = [pytest.mark.browser, pytest.mark.db]

PASSWORD = "correct-horse-battery-staple"
A_TOTAL = "₹3,790.49"


async def _register(page, email, name="Test Person"):
    await page.goto("/")
    await page.get_by_test_id("gate-switch").click()
    await page.fill("#display_name", name)
    await page.fill("#email", email)
    await page.fill("#password", PASSWORD)
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)


async def _sign_in(page, email, password):
    await page.goto("/")
    await page.wait_for_selector("#email")
    await page.fill("#email", email)
    await page.fill("#password", password)
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="whoami"]', timeout=20000)


# ── a. register, land, and the cookie ──────────────────────────────────────
async def test_a_person_can_sign_up_and_lands_on_their_dashboard(page, clean_db) -> None:
    await _register(page, "browser-a@spendwise.test", "Asha")

    assert await page.get_by_test_id("whoami").inner_text() == "Asha"

    # WAITED for, not sampled. `whoami` renders the moment the principal
    # arrives; the first-run state waits on the summary, the entry list and the
    # "has this account ever recorded anything" call. Asserting `is_visible()`
    # immediately after sign-up races all three and reports False for a state
    # that appears 80ms later.
    await page.wait_for_selector('[data-testid="state-first-run"]', timeout=20000)

    # A brand-new account: no ribbon, no bars, ONE primary action (E3-S6 AC1).
    assert await page.locator('[data-testid="ribbon"]').count() == 0
    assert await page.locator('[data-testid="daybars"]').count() == 0
    assert await page.locator('[data-testid="total"]').count() == 0


async def test_the_session_cookie_is_httponly_in_the_browsers_own_store(
        page, clean_db) -> None:
    """**Observed, not asserted about.**

    Read out of Chromium's cookie jar, and then a second, stronger check:
    `document.cookie` — the thing an XSS payload would read — must not contain
    it. That is what httpOnly MEANS, and it is the only form of this claim that
    a `set_cookie(httponly=True)` typo cannot pass.
    """
    await _register(page, "browser-cookie@spendwise.test")

    jar = [c for c in await page.context.cookies() if c["name"] == "sw_session"]
    assert jar, "no session cookie was set"
    assert jar[0]["httpOnly"] is True
    assert jar[0]["sameSite"] == "Lax"
    assert jar[0]["path"] == "/"

    visible = await page.evaluate("document.cookie")
    assert "sw_session" not in visible, (
        "the session token is readable by script — httpOnly is not in effect")


async def test_reloading_keeps_you_signed_in(page, clean_db) -> None:
    await _register(page, "browser-reload@spendwise.test", "Ravi")
    await page.reload()
    await page.wait_for_selector('[data-testid="whoami"]')
    assert await page.get_by_test_id("whoami").inner_text() == "Ravi"


async def test_signing_out_returns_to_the_gate_and_drops_the_cookie(page,
                                                                    clean_db) -> None:
    await _register(page, "browser-out@spendwise.test")
    await page.get_by_test_id("sign-out").click()
    await page.wait_for_selector("#email")
    assert not [c for c in await page.context.cookies() if c["name"] == "sw_session"]


# ── b. add an expense through the form ─────────────────────────────────────
async def test_an_expense_added_through_the_form_appears_without_a_reload(
        page, clean_db) -> None:
    """E3-S5. And it appears only AFTER the server confirms — there is no
    optimistic insert, so what is on screen is what the database holds."""
    await _register(page, "browser-add@spendwise.test")

    await page.get_by_test_id("first-add").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')

    await page.fill("input[name='amount']", "1250.00")
    await page.fill("input[name='spent_on']", "2026-08-04")
    await page.select_option("select[name='category_id']", label="Groceries")
    await page.fill("input[name='description']", "Weekly shop")
    await page.get_by_test_id("panel-submit").click()

    await page.wait_for_selector('[data-testid="entries"]', timeout=20000)
    assert await page.get_by_test_id("total").inner_text() == "₹1,250.00"
    assert await page.get_by_test_id("count").inner_text() == "1"
    listed = await page.get_by_test_id("entries").inner_text()
    assert "Weekly shop" in listed
    assert "Groceries" in listed


async def test_the_server_refuses_a_bad_amount_and_the_form_says_so(page,
                                                                    clean_db) -> None:
    """The server's own sentence, on the field the server named — not a second
    copy of the rule written in JavaScript, which is the copy nobody re-checks
    when the rule changes."""
    await _register(page, "browser-bad@spendwise.test")

    await page.get_by_test_id("first-add").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')
    await page.fill("input[name='amount']", "12.345")
    await page.get_by_test_id("panel-submit").click()

    error = page.locator(".field-error").first
    await error.wait_for(timeout=15000)
    assert await error.inner_text() == "Amount must have at most two decimal places."
    # And nothing was written.
    assert await page.locator('[data-testid="entries"]').count() == 0


async def test_escape_closes_the_panel_and_focus_returns_to_the_trigger(
        page, clean_db) -> None:
    await _register(page, "browser-esc@spendwise.test")

    await page.get_by_test_id("first-add").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')
    await page.keyboard.press("Escape")
    await page.wait_for_selector('[data-testid="expense-panel"]', state="detached")

    # WAITED FOR, not sampled. The restore runs on a zero timeout — the first
    # moment after React has cleared `inert` on the shell, because an inert
    # subtree cannot take focus at all. Reading `activeElement` the instant the
    # panel detaches races that by one tick and reports <body>.
    await page.wait_for_function(
        "document.activeElement?.dataset?.testid === 'first-add'", timeout=5000)


async def test_the_background_is_inert_while_the_panel_is_open(page, clean_db) -> None:
    """`DESIGN-SYSTEM.md §5`, observed by asking the browser what inert MEANS:
    a control in the background cannot take focus.

    The first version of this test forced a click on the sign-out button and
    asserted the panel stayed open. It failed — and the code was right. A
    forced click dispatches at the button's COORDINATES, which the scrim
    occupies, so it hit the scrim's own dismiss handler. The test was measuring
    the scrim, not inertness.
    """
    await _register(page, "browser-inert@spendwise.test")

    await page.get_by_test_id("first-add").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')

    # The whole SHELL, not the pane the dialog sits beside. The sidebar, the
    # mobile top bar and the footer sign-out are all outside the dashboard, and
    # a modal that only disabled the dashboard would leave every one of them
    # clickable behind the scrim.
    assert await page.evaluate("document.querySelector('.app').inert") is True

    landed = await page.evaluate("""
        () => {
          document.querySelector('[data-testid=sign-out]').focus()
          const el = document.activeElement
          return el?.dataset?.testid ?? el?.tagName ?? null
        }
    """)
    assert landed != "sign-out", "a background control took focus through inert"


# ── c. THE GATE, ON SCREEN ─────────────────────────────────────────────────
async def test_the_day_one_gate_is_visible_in_the_browser(page, seeded) -> None:
    """**Art IX.4, in a real browser.**

    Person A, seeded through the real endpoints, on 2026-08-05. The daily
    average is 379049 / 5 = 75810 paise, and the screen must say ₹758.10.

    Not 758.09 (truncated instead of rounding half-up) and not 947.62 (divided
    by the row count rather than days elapsed). Both are asserted, because both
    are what a plausible wrong implementation prints.
    """
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])

    average = page.get_by_test_id("daily-average")
    await average.wait_for()
    text = await average.inner_text()

    assert text == "₹758.10", f"the screen says {text!r}"
    assert text != "₹758.09", "truncated instead of rounding half-up"
    assert text != "₹947.62", "divided by the row count, not days elapsed"

    assert await page.get_by_test_id("total").inner_text() == A_TOTAL
    assert await page.get_by_test_id("count").inner_text() == "4"
    # The card wraps it ("over 5 days"); the criterion is the FIVE, which is
    # the divisor 75810 depends on.
    assert "5 days" in await page.get_by_test_id("days-elapsed").inner_text()

    # And the whole page really contains it, not just an element we happened to
    # query — the form a person would recognise.
    assert "758.10" in await page.content()


async def test_the_money_is_formatted_en_in(page, seeded) -> None:
    """`SW-ADR-056`: ₹12,34,567.89, not ₹1,234,567.89. The seeded total is
    below a lakh, so this asserts the symbol and the thousands separator; the
    lakh/crore grouping is proved arithmetically in the pure tests."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    total = page.get_by_test_id("total")
    await total.wait_for()
    assert await total.inner_text() == A_TOTAL


# ── d. person B ────────────────────────────────────────────────────────────
async def test_person_b_sees_their_own_much_smaller_number(page, seeded) -> None:
    """The product, in one assertion. B's total must not contain a paisa of
    A's — and this is the browser saying so, over HTTP, with B's own cookie."""
    await _sign_in(page, seeded["B"]["email"], seeded["B"]["password"])

    total = page.get_by_test_id("total")
    await total.wait_for()
    assert await total.inner_text() == "₹1,250.00"
    assert await page.get_by_test_id("count").inner_text() == "2"

    body = await page.content()
    assert "3,790.49" not in body, "person B's screen contains person A's money"
    assert "758.10" not in body


# ── e. the ribbon, by keyboard alone ───────────────────────────────────────
async def test_one_tab_enters_the_ribbon_and_a_second_tab_leaves_it(page,
                                                                    seeded) -> None:
    """Roving tabindex (E3-S3 AC1). Nine bands with `tabIndex=0` would be nine
    tab stops, and a keyboard user would have to press Tab nine times to get
    past a chart."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="ribbon"]')

    stops = await page.evaluate(
        "[...document.querySelectorAll('.band')].map(b => b.tabIndex)")
    assert stops.count(0) == 1, f"the ribbon has {stops.count(0)} tab stops, not 1"
    assert all(t in (0, -1) for t in stops)


async def test_arrows_home_and_end_move_between_bands(page, seeded) -> None:
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="ribbon"]')

    bands = page.locator(".band")
    count = await bands.count()
    assert count >= 2, "the fixture no longer produces more than one band"

    await bands.first.focus()
    await page.keyboard.press("ArrowRight")
    assert await page.evaluate("document.activeElement.dataset.category") \
        == await bands.nth(1).get_attribute("data-category")

    await page.keyboard.press("Home")
    assert await page.evaluate("document.activeElement.dataset.category") \
        == await bands.first.get_attribute("data-category")

    await page.keyboard.press("End")
    assert await page.evaluate("document.activeElement.dataset.category") \
        == await bands.nth(count - 1).get_attribute("data-category")


async def test_enter_filters_and_escape_clears_it_without_a_mouse(page,
                                                                  seeded) -> None:
    """E3-S3 AC3 and E3-S4: selecting a band re-scopes the total — and does NOT
    change the ribbon's own proportions (`SW-ADR-109`)."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="ribbon"]')

    whole_total = await page.get_by_test_id("total").inner_text()
    widths_before = await page.evaluate(
        "[...document.querySelectorAll('.band')].map(b => b.style.width)")

    await page.locator(".band").first.focus()
    await page.keyboard.press("Enter")
    await page.wait_for_function(
        f"document.querySelector('[data-testid=total]').innerText !== {whole_total!r}",
        timeout=15000)

    assert await page.get_by_test_id("total").inner_text() != whole_total
    assert await page.locator(".band").first.get_attribute("aria-pressed") == "true"

    # THE RIBBON DOES NOT MOVE. If it re-scoped to the filter it would collapse
    # to one band and every other band would be unreachable.
    assert await page.evaluate(
        "[...document.querySelectorAll('.band')].map(b => b.style.width)") == widths_before

    await page.keyboard.press("Escape")
    await page.wait_for_function(
        f"document.querySelector('[data-testid=total]').innerText === {whole_total!r}",
        timeout=15000)
    assert await page.locator(".band").first.get_attribute("aria-pressed") == "false"


async def test_each_band_announces_its_category_amount_and_percentage(page,
                                                                      seeded) -> None:
    """`DESIGN-SYSTEM.md §5.1` specifies the string exactly. A band is a
    rectangle of colour with no text in it, so the accessible name is the only
    name it has — and for a sliver band it is the only way to read it at all."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="ribbon"]')

    names = await page.evaluate(
        "[...document.querySelectorAll('.band')].map(b => b.getAttribute('aria-label'))")
    assert names
    for name in names:
        assert re.fullmatch(r".+: ₹[\d,]+\.\d{2}, \d+% of total", name), name


async def test_selection_is_never_signalled_by_colour_alone(page, seeded) -> None:
    """Two cues (`SW-ADR-118`): the chosen band gains an inset marker AND the
    others dim. Read out of the COMPUTED style, so a rule that was written and
    never applied does not pass."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="ribbon"]')

    await page.locator(".band").first.click()
    await page.wait_for_selector('.ribbon[data-filtering="true"]')
    # The dim is a 120ms TRANSITION. Sampling the computed style the instant
    # the attribute flips reads 1 for every band and reports both cues missing
    # when both are present — which is what the first version of this test did.
    await page.wait_for_function(
        "getComputedStyle(document.querySelectorAll('.band')[1]).opacity !== '1'",
        timeout=5000)

    chosen_opacity = await page.evaluate(
        "getComputedStyle(document.querySelectorAll('.band')[0]).opacity")
    other_opacity = await page.evaluate(
        "getComputedStyle(document.querySelectorAll('.band')[1]).opacity")
    chosen_shadow = await page.evaluate(
        "getComputedStyle(document.querySelectorAll('.band')[0]).boxShadow")

    assert float(other_opacity) < float(chosen_opacity), "cue 1 (dimming) is absent"
    assert "inset" in chosen_shadow, "cue 2 (the marker) is absent"
    assert await page.locator(".band").nth(0).get_attribute("aria-pressed") == "true"
    assert await page.locator(".band").nth(1).get_attribute("aria-pressed") == "false"


# ── the period, and the URL ────────────────────────────────────────────────
async def test_the_period_lives_in_the_url_and_survives_a_reload(page,
                                                                 seeded) -> None:
    """E3-S2. `This month` on 2026-08-05 in Asia/Kolkata is 1–31 August."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="headline"]')

    assert "from=2026-08-01" in page.url
    assert "to=2026-08-31" in page.url

    await page.get_by_test_id("period-last-month").click()
    await page.wait_for_function("location.search.includes('from=2026-07-01')",
                                 timeout=15000)

    await page.reload()
    await page.wait_for_selector('[data-testid="headline"]')
    assert "from=2026-07-01" in page.url
    assert await page.get_by_test_id("period-last-month").get_attribute("aria-pressed") \
        == "true"


async def test_the_back_button_returns_to_the_previous_period(page, seeded) -> None:
    """AC3, and the reason the period is in the URL rather than in component
    state: with component state, Back leaves the application."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="headline"]')

    await page.get_by_test_id("period-last-month").click()
    await page.wait_for_function("location.search.includes('from=2026-07-01')",
                                 timeout=15000)

    await page.go_back()
    await page.wait_for_function("location.search.includes('from=2026-08-01')",
                                 timeout=15000)
    assert await page.get_by_test_id("whoami").is_visible(), "Back left the application"
    await page.wait_for_function(
        f"document.querySelector('[data-testid=total]')?.innerText === {A_TOTAL!r}",
        timeout=15000)


# ── f. phone width ─────────────────────────────────────────────────────────
async def test_nothing_overflows_at_375px(phone, seeded) -> None:
    """E3-S8 AC1. Measured, not styled around: `scrollWidth > clientWidth` is
    the browser telling you the page is wider than the window, and
    `overflow-x: hidden` would hide that rather than fix it."""
    await _sign_in(phone, seeded["A"]["email"], seeded["A"]["password"])
    await phone.wait_for_selector('[data-testid="headline"]')

    overflow = await phone.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 0, f"the page is {overflow}px wider than a 375px window"

    # And no individual element sticks out of it either — a child can overflow
    # its own scroll container while the document's scrollWidth stays put.
    strays = await phone.evaluate("""
        [...document.querySelectorAll('body *')]
          .filter(el => el.getBoundingClientRect().right > 375.5)
          .map(el => el.tagName + '.' + (el.className || ''))
          .slice(0, 5)
    """)
    assert not strays, f"elements extend past 375px: {strays}"


async def test_every_interactive_target_is_at_least_44px_at_phone_width(
        phone, seeded) -> None:
    """AC3. 44×44 CSS px is the WCAG 2.1 AA floor `SW-ADR-117` adopts. The
    ribbon bands are the sanctioned exception: `SW-ADR-055` keeps them
    true-proportion, and a sliver band's reachability is the keyboard's job."""
    await _sign_in(phone, seeded["A"]["email"], seeded["A"]["password"])
    await phone.wait_for_selector('[data-testid="headline"]')

    small = await phone.evaluate("""
        [...document.querySelectorAll('button, a, select, input')]
          .filter(el => !el.classList.contains('band'))
          .filter(el => el.offsetParent !== null)
          .map(el => ({ what: el.tagName + '.' + (el.className || ''),
                        w: Math.round(el.getBoundingClientRect().width),
                        h: Math.round(el.getBoundingClientRect().height) }))
          .filter(m => m.w < 44 || m.h < 44)
    """)
    assert not small, f"targets below 44x44: {small}"


async def test_the_panel_enters_from_the_bottom_at_phone_width(phone, clean_db) -> None:
    """`DESIGN-SYSTEM.md §7`. Observed as geometry — the panel's bottom edge
    sits at the bottom of the window — rather than by reading the animation
    name, because a keyframe declared and never applied would pass that."""
    await _register(phone, "browser-phone@spendwise.test")

    await phone.get_by_test_id("first-add").click()
    await phone.wait_for_selector('[data-testid="expense-panel"]')
    # Let the entry animation settle; the assertion is about the resting place.
    await phone.wait_for_timeout(400)

    box = await phone.get_by_test_id("expense-panel").bounding_box()
    height = await phone.evaluate("window.innerHeight")
    assert abs((box["y"] + box["height"]) - height) < 2, (
        f"the panel's bottom is at {box['y'] + box['height']}, not at {height}")
    assert box["x"] < 2, "the panel is inset from the left — it came from the side"


# ── the states nobody wants to see ─────────────────────────────────────────
async def test_a_failed_summary_shows_an_error_and_never_renders_zero(page,
                                                                      seeded) -> None:
    """**E3-S6 AC3, the sharpest rule on the screen.**

    A zero where a total should be is indistinguishable from "you spent
    nothing", and it is the number a person acts on. Retry preserves the
    period, because the period is in the URL.
    """
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="headline"]')

    async def fail(route):
        await route.fulfill(
            status=500, content_type="application/json",
            body='{"error":{"code":"INTERNAL","message":"Something went wrong."}}')

    await page.route("**/api/expenses/summary*", fail)

    await page.get_by_test_id("period-last-month").click()
    await page.wait_for_selector('[data-testid="state-error"]', timeout=15000)

    body = await page.content()
    assert "0.00" not in body, "a zero total was rendered over a failed request"
    assert "₹0" not in body
    assert await page.locator('[data-testid="total"]').count() == 0

    # Retry, with the route restored, comes back to the SAME period.
    await page.unroute("**/api/expenses/summary*")
    await page.get_by_test_id("retry").click()
    await page.wait_for_selector('[data-testid="headline"]', timeout=20000)
    assert "from=2026-07-01" in page.url


async def test_a_session_that_ends_mid_use_routes_to_sign_in_with_a_reason(
        page, seeded) -> None:
    """E3-S7 AC1 and AC2. Every API call 401s at once — the dashboard fires
    three in parallel — and exactly ONE redirect happens, carrying one banner."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="headline"]')

    async def gone(route):
        await route.fulfill(
            status=401, content_type="application/json",
            body='{"error":{"code":"SESSION_INVALID",'
                 '"message":"Your session has ended. Please sign in again."}}')

    await page.route("**/api/**", gone)

    await page.get_by_test_id("period-last-month").click()
    await page.wait_for_selector('[data-testid="session-reason"]', timeout=15000)

    assert await page.locator('[data-testid="session-reason"]').count() == 1
    reason = await page.get_by_test_id("session-reason").inner_text()
    assert "session ended" in reason.lower()
    assert await page.locator("#email").is_visible()


async def test_a_half_typed_expense_survives_the_session_ending(page, seeded) -> None:
    """AC3. Held above the screen that gets unmounted — inside the dashboard it
    would be destroyed by the very navigation it needs to survive."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="headline"]')

    await page.get_by_test_id("add-expense").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')
    await page.fill("input[name='amount']", "432.10")
    await page.fill("input[name='description']", "Half typed")

    async def gone(route):
        await route.fulfill(
            status=401, content_type="application/json",
            body='{"error":{"code":"SESSION_INVALID","message":"Your session has ended."}}')

    await page.route("**/api/**", gone)
    await page.get_by_test_id("panel-submit").click()
    await page.wait_for_selector('[data-testid="session-reason"]', timeout=15000)

    # Sign back in; the draft is still there.
    await page.unroute("**/api/**")
    await page.fill("#email", seeded["A"]["email"])
    await page.fill("#password", seeded["A"]["password"])
    await page.get_by_test_id("gate-submit").click()
    await page.wait_for_selector('[data-testid="headline"]', timeout=20000)

    await page.get_by_test_id("add-expense").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')

    # WAITED for. `wait_for_selector` resolves on the first render in which the
    # panel exists, and the form is populated by an effect — which React runs
    # after that render commits. Sampling `input_value` immediately reads the
    # empty initial state, and does so only when the machine is busy enough for
    # the two to land in different frames. The same race as the ribbon's
    # opacity transition and the focus restore, and the same fix.
    await page.wait_for_function(
        "document.querySelector(\"input[name='amount']\")?.value === '432.10'",
        timeout=5000)
    assert await page.input_value("input[name='description']") == "Half typed"


async def test_a_filter_matching_nothing_is_a_different_state_from_a_new_account(
        page, seeded) -> None:
    """E3-S6 AC2. Written as one "empty" component these are identical — and
    then a person with a year of history is told they have never spent
    anything."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="headline"]')

    # A category with no spending in the period. Entertainment (6) is seeded
    # for everyone and used by nobody in the fixture.
    await page.goto("/?from=2026-08-01&to=2026-08-31&category=6")
    await page.wait_for_selector('[data-testid="state-no-matches"]', timeout=20000)

    assert await page.locator('[data-testid="state-first-run"]').count() == 0
    assert await page.get_by_test_id("state-no-matches").is_visible()
    # The headline still shows — a filtered zero is a real, correct zero, and
    # the state that must never show 0.00 is the FAILED one, not this.
    assert await page.get_by_test_id("total").inner_text() == "₹0.00"


# ── editing and deleting, through the screen ───────────────────────────────
async def test_an_expense_can_be_edited_and_the_total_follows(page, seeded) -> None:
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="entries"]')

    first = seeded["A"]["expenses"][0]
    await page.get_by_test_id(f"edit-{first['id']}").click()
    await page.wait_for_selector('[data-testid="expense-panel"]')
    await page.fill("input[name='amount']", "1.00")
    await page.get_by_test_id("panel-submit").click()

    expected = 379049 - first["amount_paise"] + 100
    want = f"₹{expected // 100:,}.{expected % 100:02d}"
    await page.wait_for_function(
        f"document.querySelector('[data-testid=total]').innerText === {want!r}",
        timeout=20000)


async def test_deleting_asks_first_and_names_the_amount(page, seeded) -> None:
    """`SW-ADR-119`: a destructive action names its blast radius before it
    runs. Dismissing the confirm must change nothing."""
    await _sign_in(page, seeded["A"]["email"], seeded["A"]["password"])
    await page.wait_for_selector('[data-testid="entries"]')

    first = seeded["A"]["expenses"][0]
    messages = []

    async def dismiss(d):
        messages.append(d.message)
        await d.dismiss()

    page.once("dialog", dismiss)
    await page.get_by_test_id(f"delete-{first['id']}").click()
    await page.wait_for_timeout(1000)

    assert messages, "no confirmation was shown before a delete"
    assert "₹" in messages[0], "the confirm did not name the amount"
    assert await page.get_by_test_id("total").inner_text() == A_TOTAL, "dismiss deleted it"

    async def accept(d):
        await d.accept()

    page.once("dialog", accept)
    await page.get_by_test_id(f"delete-{first['id']}").click()
    await page.wait_for_function(
        "document.querySelector('[data-testid=count]').innerText === '3'", timeout=20000)


# ── the ops endpoints, over a real socket ──────────────────────────────────
async def test_healthz_and_readyz_answer_over_http(app_server) -> None:
    """In-process they are the same code. Over a socket they are also the thing
    a container health check and a deploy script actually call."""
    import httpx

    async with httpx.AsyncClient(base_url=app_server) as c:
        health = await c.get("/healthz")
        assert health.status_code == 200
        assert health.content == b""

        ready = (await c.get("/readyz")).json()
    assert ready["status"] == "ready"
    assert ready["revision"]
    assert ready["build"] == "browser-test"
