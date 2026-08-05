"""`CR-001` / `SW-ADR-151` — the grant, and its boundary.

The client reversed their own permission matrix. `SRC-001 §4.2` said, in their
words and their bold:

    | See anyone else's expense amounts | user: no | admin: **no** |

`CR-001` says instead:

> they can see **the expenses that are happening not the categories spent on**
> so the will be able to see the line plot for that particular user and have the
> filter option to see the line plot based on time filter.

Two halves. The first is granted here and asserted with real numbers — an
administrator reading person A's August must get **379049**, the day-one figure,
not a plausible zero. The second is refused here and asserted mechanically: no
category, no description, at any granularity, in the model or in the bytes.

The half that is easiest to get wrong is neither: it is `SW-ADR-149`. Every
query in this system runs under row-level security keyed on `app.user_id`, and
`app.user_id` holds the **administrator's** id. A cross-user read that forgets
the identity swap returns an empty result and reports success — a line plot of
nothing, for every account but the reader's own. So the tests here assert the
*values*, and one of them asserts them against the person's own summary fetched
in the same test. Asserting the response SHAPE proves nothing at all.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from tests.seed import seed

pytestmark = [pytest.mark.db]

# `SW-ADR-039` freezes the day-one figures to 2026-08-05: `days_elapsed` is
# `min(to, today) - from + 1`, so the divisor grows by one every midnight and
# 379049 / 5 = 75810 holds ON THAT DAY and no other.
GATE_DAY = "2026-08-05"

MONTH = "from=2026-08-01&to=2026-08-31"
# Two days, one expense. Narrower in both directions: fewer rows AND a smaller
# divisor, so a handler that filtered the rows and forgot the denominator gives
# a different wrong answer than one that did neither.
NARROW = "from=2026-08-01&to=2026-08-02"

# Person A's August, from `contract.json`'s seed fixture. Typed here only as the
# expectation; the seed itself reads the contract.
A_TOTAL, A_COUNT, A_ELAPSED, A_AVERAGE = 379049, 4, 5, 75810
A_NARROW_TOTAL, A_NARROW_COUNT, A_NARROW_AVERAGE = 125000, 1, 62500
B_TOTAL, B_COUNT = 125000, 2

# The three descriptions and three category names person A's rows carry. If any
# of these reaches an admin response, `CR-001`'s line has been crossed.
A_DESCRIPTIONS = ("Weekly shop", "Auto to office", "Pharmacy")
A_CATEGORIES = ("Groceries", "Transport", "Health")


@pytest.fixture(autouse=True)
def _frozen_to_the_gate_day(monkeypatch):
    """Pin `today`. **Autouse, so it runs before `client`** — which clears the
    settings cache and re-imports the app, and would otherwise bake in the real
    date.

    Every number in this file is a function of the current date. Without this
    the file passes on the day it is written and fails at the next midnight with
    no code change behind it, which is the failure `CV-14` added
    `APP_TODAY_OVERRIDE` to prevent and which `test_gate_75810.py` has already
    been bitten by once.
    """
    monkeypatch.setenv("APP_TODAY_OVERRIDE", GATE_DAY)


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


async def _make_admin(client, clean_db, test_urls, who: str = "B"):
    """Seed both people, promote one by hand as the owner, and sign them in.

    **`B` is the administrator here and `A` is the subject**, which is the
    opposite of `test_admin.py`'s default and deliberate: A owns the day-one
    fixture, so every read in this file is a genuine CROSS-user read with known
    expected values. An administrator reading their own row would pass every
    assertion in this file with the identity swap deleted (`SW-ADR-149`).
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    made = await seed(client, guard_database=clean_db)
    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("UPDATE users SET role = 'admin' WHERE id = :i"),
                        {"i": made[who]["id"]})
    await e.dispose()
    await _sign_in(client, made[who])
    return made


@asynccontextmanager
async def _as(who: dict):
    """A SECOND httpx client, signed in as the person themselves.

    The comparison this file keeps making — "the admin's number is the number
    the person sees" — needs both answers in one test, and they come from two
    sessions. Fetching them rather than restating a constant is what proves the
    admin path is not a second implementation of the same arithmetic that
    happens to agree today.
    """
    import httpx

    from app.main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://testserver") as c:
        await _sign_in(c, who)
        yield c


def _spending(user_id: int, query: str = MONTH) -> str:
    return f"/api/admin/users/{user_id}/spending?{query}"


# ── the grant ──────────────────────────────────────────────────────────────
async def test_the_admin_sees_the_person_s_real_total_and_THEIR_average(
        client, clean_db, test_urls) -> None:
    """**The change request, and the proof it is not a second implementation.**

    The four figures are person A's day-one fixture: 379049 over 4 entries,
    5 days elapsed, 75810 a day. 75810 is the gate number — the one
    `CONSTITUTION` Art IX.4 makes never-waivable — so if the admin path rounds
    differently, truncates, or divides by the row count instead of the days,
    this fails on a value the whole project already agrees about.

    Then the same range is fetched **as person A** and the averages compared.
    That is the assertion that matters: `CR-001 §2` requires `days_elapsed` and
    the half-up average to come from `app/core/clock.py` and `app/core/money.py`
    — the same helpers the person's own summary uses. A reimplementation would
    pass the constants above on the day it was written and drift on the first
    range where half-up and truncation disagree, which is most of them.
    """
    made = await _make_admin(client, clean_db, test_urls)

    r = await client.get(_spending(made["A"]["id"]))
    assert r.status_code == 200, r.text
    got = r.json()

    assert got["total_paise"] == A_TOTAL
    assert got["total"] == "3790.49"
    assert got["count"] == A_COUNT
    assert got["days_elapsed"] == A_ELAPSED
    assert got["daily_average_paise"] == A_AVERAGE
    assert got["daily_average"] == "758.10"
    assert got["from"] == "2026-08-01" and got["to"] == "2026-08-31"

    # Who they are, from `CR-001 §2`'s `user` block.
    assert got["user"]["id"] == made["A"]["id"]
    assert got["user"]["email"] == made["A"]["email"]
    assert got["user"]["is_active"] is True
    assert got["user"]["deleted"] is False

    async with _as(made["A"]) as them:
        mine = (await them.get(f"/api/expenses/summary?{MONTH}")).json()

    assert got["daily_average_paise"] == mine["daily_average_paise"], (
        "the admin's average is not the person's own — CR-001 §2 says the same "
        "half-up helper computes both, and a second implementation is how a "
        "truncating average appears (75810 becomes 75809, wrongly)")
    assert got["daily_average"] == mine["daily_average"]
    assert got["days_elapsed"] == mine["days_elapsed"]
    assert got["total_paise"] == mine["total_paise"]
    assert got["count"] == mine["count"]


async def test_the_response_carries_no_category_and_no_description(
        client, clean_db, test_urls) -> None:
    """**The half `CR-001` refused**, asserted over the raw bytes.

    > the expenses that are happening **not the categories spent on**

    `by_category` is checked for absence as a KEY, and the seeded descriptions
    and category names are grepped out of the response TEXT — because the way
    this leaks is not a documented field, it is a debug key, a nested `user`
    object that grew, or a serialiser that dumps the ORM row.

    The control at the bottom is not decoration: it fetches the same strings
    through the person's OWN endpoints and asserts they are there. Without it,
    a grep for "Weekly shop" that finds nothing proves the string is absent from
    the system, not from this response — and the seed changing a description
    would turn this test green forever.
    """
    made = await _make_admin(client, clean_db, test_urls)

    r = await client.get(_spending(made["A"]["id"]))
    assert r.status_code == 200, r.text
    body, raw = r.json(), r.text

    assert "by_category" not in body, "CR-001: no category breakdown, at any granularity"
    assert "categor" not in raw.lower(), (
        f"a category-shaped key or value reached the admin spending response: "
        f"{raw[:400]!r}")

    for word in A_DESCRIPTIONS:
        assert word not in raw, f"the admin response leaked the description {word!r}"
    for name in A_CATEGORIES:
        assert name not in raw, f"the admin response leaked the category {name!r}"

    # The probe works: those strings ARE reachable — by the person who owns them.
    async with _as(made["A"]) as them:
        rows = await them.get("/api/expenses")
        summary = await them.get(f"/api/expenses/summary?{MONTH}")
    assert "Weekly shop" in rows.text, "the seed no longer carries the descriptions"
    assert "Groceries" in summary.text, "the seed no longer carries the categories"


async def test_every_day_in_the_range_appears_including_the_empty_ones(
        client, clean_db, test_urls) -> None:
    """`CR-001 §2`: every day, including zeroes — same as the person's summary.

    A line plot drawn from a gap-free series is a line; drawn from only the days
    with spending it is a **different shape entirely**, because the x-axis
    silently becomes ordinal instead of temporal and three days of nothing
    render as one flat step.

    In SQL this is `generate_series` LEFT JOINed to `expenses` with the owner
    predicate in `ON` and never in `WHERE` — in `WHERE` the LEFT JOIN degenerates
    to an INNER JOIN and the zero days vanish without an error.
    """
    made = await _make_admin(client, clean_db, test_urls)
    by_day = (await client.get(_spending(made["A"]["id"]))).json()["by_day"]

    assert len(by_day) == 31, f"August has 31 days; got {len(by_day)}"
    assert [d["date"] for d in by_day] == [
        f"2026-08-{n:02d}" for n in range(1, 32)], "the series has a gap"

    seen = {d["date"]: d for d in by_day}
    assert seen["2026-08-01"] == {"date": "2026-08-01", "total_paise": 125000, "count": 1}
    assert seen["2026-08-02"] == {"date": "2026-08-02", "total_paise": 0, "count": 0}
    # 34050 + 210000, two entries on one day.
    assert seen["2026-08-03"] == {"date": "2026-08-03", "total_paise": 244050, "count": 2}
    assert seen["2026-08-05"] == {"date": "2026-08-05", "total_paise": 9999, "count": 1}
    assert seen["2026-08-31"]["total_paise"] == 0

    assert sum(d["total_paise"] for d in by_day) == A_TOTAL, (
        "the days do not add up to the headline — the plot and the number "
        "beside it would disagree on screen")
    assert sum(d["count"] for d in by_day) == A_COUNT


async def test_a_narrower_range_returns_less_and_still_agrees_with_their_summary(
        client, clean_db, test_urls) -> None:
    """The **time filter**, which is the third thing the client asked for.

    Narrowing to the 1st-2nd drops three of the four entries AND the divisor,
    from 5 days to 2. Both have to move: a handler that filtered the rows but
    kept the month's `days_elapsed` would report 25000 a day, which is wrong and
    entirely plausible.

    Compared against person A's own summary for the same narrower range, for the
    same reason as the month — one arithmetic, reached two ways.
    """
    made = await _make_admin(client, clean_db, test_urls)

    wide = (await client.get(_spending(made["A"]["id"], MONTH))).json()
    narrow = (await client.get(_spending(made["A"]["id"], NARROW))).json()

    assert narrow["total_paise"] == A_NARROW_TOTAL
    assert narrow["count"] == A_NARROW_COUNT
    assert narrow["days_elapsed"] == 2
    assert narrow["daily_average_paise"] == A_NARROW_AVERAGE
    assert len(narrow["by_day"]) == 2
    assert narrow["total_paise"] < wide["total_paise"], "the filter changed nothing"

    async with _as(made["A"]) as them:
        mine = (await them.get(f"/api/expenses/summary?{NARROW}")).json()
    assert narrow["total_paise"] == mine["total_paise"]
    assert narrow["days_elapsed"] == mine["days_elapsed"]
    assert narrow["daily_average_paise"] == mine["daily_average_paise"]
    assert [d["date"] for d in narrow["by_day"]] == [d["date"] for d in mine["by_day"]]


# ── the range rules, which are not new rules ───────────────────────────────
@pytest.mark.parametrize(("query", "field"), [
    pytest.param("from=2026-08-31&to=2026-08-01", "to", id="range.order"),
    # 401 days inclusive of both ends — one past the cap, which is measured on
    # `span = (to - from).days + 1` and is therefore an off-by-one waiting to
    # happen in any second implementation.
    pytest.param("from=2026-01-01&to=2027-02-05", "to", id="range.span"),
    pytest.param("from=1999-12-31&to=2000-01-01", "from", id="range.floor"),
])
async def test_the_range_rules_are_the_SAME_ones_the_person_s_summary_enforces(
        client, clean_db, test_urls, query, field) -> None:
    """`CR-001 §2`: "Range rules are the SAME as `/api/expenses/summary`. Reuse
    `validate_summary_query`."

    So the assertion is **equality of the two bodies**, not two independent
    checks that both happen to say 422. A second copy of these rules would agree
    on the three cases anybody thinks to write and disagree on precedence — and
    precedence is exactly what `SW-ADR-141` was written about: two engineers
    implementing opposite orders both pass a negative suite where every case
    varies one input.
    """
    made = await _make_admin(client, clean_db, test_urls)

    theirs = await client.get(_spending(made["A"]["id"], query))
    async with _as(made["A"]) as them:
        own = await them.get(f"/api/expenses/summary?{query}")

    assert theirs.status_code == 422, theirs.text
    assert theirs.json()["error"]["field"] == field
    assert own.status_code == 422, own.text
    assert theirs.json() == own.json(), (
        "the admin range rules answer differently from the person's own — "
        "CR-001 §2 says they are the same rules, reached through the same helper")


async def test_a_missing_range_is_refused_rather_than_guessed(client, clean_db,
                                                              test_urls) -> None:
    """`range.required`: *"Both from and to are required; there is no default
    range."*

    A default would be the worst possible kindness here. "This month" as an
    implicit range makes an administrator's screenshot undated, and the first
    person to compare two of them across a month boundary would find two
    different numbers for the same question.
    """
    made = await _make_admin(client, clean_db, test_urls)

    theirs = await client.get(f"/api/admin/users/{made['A']['id']}/spending")
    async with _as(made["A"]) as them:
        own = await them.get("/api/expenses/summary")

    assert theirs.status_code == 422, theirs.text
    assert own.status_code == 422, own.text
    assert theirs.json() == own.json(), (
        "a missing range is answered differently on the two endpoints")


# ── who may ask ────────────────────────────────────────────────────────────
async def test_a_plain_user_is_refused_and_a_stranger_is_401_not_403(
        client, clean_db, test_urls) -> None:
    """`require_admin`, on the router, as always (`SRC-001 §4.3`).

    The order of the two matters: answering 403 to someone who has not
    identified themselves at all would confirm the route exists — and this is
    the one route in the product that reads another person's money.

    A `user` is refused **even for their own id**. "It is only my own data" is
    true and irrelevant: `/api/expenses/summary` is where a person reads their
    own money, and a second door into the same number that happens to be
    admin-shaped is a door somebody will forget to lock.
    """
    made = await seed(client, guard_database=clean_db)

    stranger = await client.get(_spending(made["A"]["id"]))
    assert stranger.status_code == 401, stranger.text
    assert stranger.json()["error"]["code"] == "UNAUTHENTICATED"

    await _sign_in(client, made["B"])
    refused = await client.get(_spending(made["A"]["id"]))
    assert refused.status_code == 403, refused.text
    assert refused.json()["error"]["code"] == "FORBIDDEN"

    own = await client.get(_spending(made["B"]["id"]))
    assert own.status_code == 403, "a user reached an admin route for their own id"


async def test_an_unknown_account_is_404(client, clean_db, test_urls) -> None:
    """`P-PRV-03`: not-found and not-visible are the same refusal. An
    administrator can see every account, so here the two genuinely coincide —
    and the shape is kept identical so they never diverge."""
    await _make_admin(client, clean_db, test_urls)
    r = await client.get(_spending(999999))
    assert r.status_code == 404, r.text
    assert r.json()["error"]["code"] == "NOT_FOUND"


# ── the audit ──────────────────────────────────────────────────────────────
async def test_reading_a_person_s_spending_writes_exactly_ONE_audit_row(
        client, clean_db, test_urls) -> None:
    """`CR-001 §2`, and the plainest sentence in the change request:

    > it is a reduction in privacy that was previously ruled out, taken
    > deliberately, and every read of it is written to the audit log.

    **The delta is TWO, not one**, and the arithmetic is the same subtlety
    `test_reading_the_user_list_writes_exactly_one_read_audit_row` documents:
    each audit read reports the total as it stood BEFORE its own row is written
    — deliberately, so a reader never finds the record of their own read inside
    the page that produced it. So the delta is the spending read (1) plus the
    first audit read's own row (1).

    `users_list_viewed`, not a tenth action: the nine-item allowlist in
    `admin_audit_log`'s CHECK constraint is CLOSED, and adding a capability
    means a migration rather than a new string (`E4-S5` AC4).
    """
    made = await _make_admin(client, clean_db, test_urls)

    before = (await client.get("/api/admin/audit")).json()["total"]
    r = await client.get(_spending(made["A"]["id"]))
    assert r.status_code == 200, r.text
    after = (await client.get("/api/admin/audit")).json()["total"]

    assert after - before == 2, (
        f"{before} -> {after}: the spending read wrote {after - before - 1} audit "
        f"rows, not one")

    page = (await client.get("/api/admin/audit")).json()
    reads = [row for row in page["items"] if row["action"] == "users_list_viewed"]
    assert len(reads) == 1, (
        "the spending read did not write `users_list_viewed` — a tenth action "
        "would be refused by the CHECK constraint, as an IntegrityError that "
        "takes the read with it")
    assert "{" not in reads[0]["sentence"], "raw JSON reached the audit sentence"


# ── SW-ADR-149: the bug that returns a plausible nothing ───────────────────
async def test_the_answer_is_the_TARGET_S_money_and_not_the_CALLER_S(
        client, clean_db, test_urls) -> None:
    """**`SW-ADR-149`, and the reason every other test in this file asserts
    values rather than keys.**

    `app.user_id` holds the ADMINISTRATOR's id on every request. A query that
    reads `expenses` without swapping it returns **zero rows under row-level
    security and raises nothing** — a spending pane that is correctly shaped,
    correctly dated, entirely empty, and reports 200. That exact failure has
    already happened twice in this codebase: `admin_revoke_sessions` signed
    nobody out and said it had, and `sessions` returned "nobody is signed in".

    So: the administrator is person **B**, and B asks about person **A**.

    * A's month must come back as A's — 379049 over 4 entries.
    * It must NOT be B's 125000, which is what a swap to the wrong target gives.
    * It must not be empty, which is what no swap at all gives.
    * And B's own row must still answer correctly afterwards, which is what
      proves the GUC was RESTORED and not merely set — `admin_user_daily` swaps
      `app.user_id` and puts it back, exactly like `admin_expense_stats`.
    """
    made = await _make_admin(client, clean_db, test_urls)
    a, b = made["A"]["id"], made["B"]["id"]

    r = await client.get(_spending(a))
    # Status FIRST. Indexing an error envelope raises `KeyError: 'user'`, which
    # reports a missing field on a response that was never a spending response
    # — and sends the reader looking at the schema instead of at the 401.
    assert r.status_code == 200, r.text
    theirs = r.json()
    assert theirs["user"]["id"] == a
    assert theirs["total_paise"] == A_TOTAL, (
        f"asked for user #{a}'s August and got {theirs['total_paise']} — "
        f"0 means no identity swap, {B_TOTAL} means the caller's own rows")
    assert theirs["count"] == A_COUNT
    assert theirs["total_paise"] != B_TOTAL
    assert any(d["total_paise"] > 0 for d in theirs["by_day"]), (
        "every day is zero: the plot would render as a flat line and the screen "
        "would report it as 'this person spent nothing'")

    own = await client.get(_spending(b))
    assert own.status_code == 200, own.text
    mine = own.json()
    assert mine["total_paise"] == B_TOTAL and mine["count"] == B_COUNT, (
        "the administrator's own figures are wrong too — the swap did not "
        "restore app.user_id")

    # And the identity really is back: an ordinary admin read still works.
    assert (await client.get("/api/admin/users")).status_code == 200
    assert (await client.get("/api/auth/me")).json()["id"] == b


async def test_a_closed_account_can_still_be_read(client, clean_db, test_urls) -> None:
    """The account list keeps closed accounts (`CR-001 §2`), so the detail pane
    behind it has to answer for one too.

    An administrator deciding whether to restore somebody is exactly the person
    who needs to look first, and a 404 here would make the `deleted` flag on the
    list a row you can see and cannot open.
    """
    made = await _make_admin(client, clean_db, test_urls)

    async with _as(made["A"]) as them:
        assert (await them.delete("/api/auth/me")).status_code == 204

    r = await client.get(_spending(made["A"]["id"]))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["deleted"] is True
    assert body["user"]["is_active"] is False
    assert body["total_paise"] == A_TOTAL, (
        "closing the account changed the figures — CR-001 is a SOFT delete and "
        "every row survives it")
