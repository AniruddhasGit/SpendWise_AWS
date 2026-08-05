"""`CR-001` / `SW-ADR-150` — closing an account, without losing it.

`SW-ADR-107` ruled that user deletion does not exist in v1 — and has since been
superseded by `SW-ADR-150`, which is why this file exists at all:

> Deleting a person's financial history is the clearest one-way door in the
> register. […] When deletion comes, it arrives as a client-run runbook plus a
> superseding ADR.

The client has now asked for deletion and **named its form — soft**, which is
the version that does not walk through that door. So every test here is really
one assertion said eight ways: *the account closes and the rows stay*. The
failure mode this file exists to prevent is a `DELETE` that means what the word
usually means, and the second is a "Delete" button wired to `/deactivate`, which
would be a lie told to the one person entitled to the truth.

The distinction is asserted at the **database**, over an owner connection, not
by reading the response — a 204 is the same 204 either way, and `SW-ADR-149`
records what this codebase's silent failures look like.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import pytest

from tests.seed import seed

pytestmark = [pytest.mark.db]

COOKIE = "sw_session"                                   # `CV-01`, auth.service


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


async def _promote(test_urls, user_id: int) -> None:
    """Make someone an administrator by hand, as the owner.

    Direct SQL rather than an endpoint, for the reason `test_admin.py` gives:
    promoting requires an administrator, and this is how the first one is made
    without coupling every test here to `BOOTSTRAP_ADMIN_EMAIL`.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("UPDATE users SET role='admin' WHERE id=:i"), {"i": user_id})
    await e.dispose()


@asynccontextmanager
async def _owner_reading_as(test_urls, user_id: int):
    """An OWNER connection inside a transaction, with `app.user_id` set.

    The pattern is `test_account_settings.py::test_deactivating_keeps_every_row`'s,
    and the GUC is **not** a formality: `expenses`, `categories` and `sessions`
    are all under row-level security, and `sessions` under FORCE ROW LEVEL
    SECURITY — which applies to the table owner too (`SW-ADR-136 B`). Without it
    every count below reads 0, and "the money survived" would be asserted
    against an empty result set.

    `set_config(..., true)` is TRANSACTION-local, so the transaction is part of
    the mechanism rather than tidiness.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    try:
        async with e.connect() as c, c.begin():
            await c.execute(text("SELECT set_config('app.user_id', :u, true)"),
                            {"u": str(user_id)})
            yield c
    finally:
        await e.dispose()


# ── the endpoint ───────────────────────────────────────────────────────────
async def test_closing_your_account_is_204_clears_the_cookie_and_kills_the_session(
        client, clean_db, test_urls) -> None:
    """`CR-001 §2`: 204, no body, cookie cleared, every session revoked.

    Three separate facts, and the third is the one that can rot silently. The
    cookie being cleared is a header; the session being dead is a **row**, and
    a handler that only cleared the cookie would look identical here — right up
    until someone replayed the token (`NEG-A-03`). So the revocation is asserted
    against `sessions.revoked_at` over an owner connection, not inferred from a
    401 that a missing cookie would also produce.
    """
    from sqlalchemy import text

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert client.cookies.get(COOKIE), "the sign-in did not set a cookie to clear"

    r = await client.delete("/api/auth/me")
    assert r.status_code == 204, r.text
    assert r.content == b"", "204 NO CONTENT carried a body"

    header = r.headers.get("set-cookie", "")
    assert COOKIE in header, f"the response did not clear the cookie: {header!r}"
    assert "max-age=0" in header.lower(), header
    assert not client.cookies.get(COOKIE), "the browser would still hold a session cookie"

    assert (await client.get("/api/auth/me")).status_code == 401

    async with _owner_reading_as(test_urls, made["A"]["id"]) as c:
        live = (await c.execute(text(
            "SELECT count(*) FROM sessions WHERE user_id = :u AND revoked_at IS NULL"),
            {"u": made["A"]["id"]})).scalar()
        total = (await c.execute(text("SELECT count(*) FROM sessions WHERE user_id = :u"),
                                 {"u": made["A"]["id"]})).scalar()
    assert total >= 1, "no session rows at all — the GUC or the seed is wrong"
    assert live == 0, f"{live} of {total} sessions survived the close"


async def test_closing_an_account_keeps_every_row(client, clean_db, test_urls) -> None:
    """**The whole change request, in one assertion.**

    `SW-ADR-107` — superseded by `SW-ADR-150` — called hard deletion the clearest
    one-way door in the register;
    `CR-001` asked for the soft form by name. So: the expenses are there, the
    categories are there, the person's own row is there — and the only
    difference is two columns.

    `deleted_at` AND `is_active` together, because they are two facts and this
    system reads them in different places. `count_active_admins`, the overview's
    counts and `set_active`'s last-admin guard are all `is_active`-shaped; a
    close that set only `deleted_at` would leave every one of them counting a
    closed account as a live one.
    """
    from sqlalchemy import text

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert (await client.delete("/api/auth/me")).status_code == 204

    async with _owner_reading_as(test_urls, made["A"]["id"]) as c:
        expenses = (await c.execute(text("SELECT count(*) FROM expenses"))).scalar()
        cats = (await c.execute(text("SELECT count(*) FROM categories"))).scalar()
        row = (await c.execute(text(
            "SELECT is_active, deleted_at FROM users WHERE id = :i"),
            {"i": made["A"]["id"]})).one_or_none()

    assert row is not None, "the person's row was DELETED — CR-001 asked for soft"
    is_active, deleted_at = row
    assert expenses == 4, "closing the account destroyed the money"
    assert cats == 8, "closing the account destroyed the categories"
    assert deleted_at is not None, "deleted_at was never set — this was a deactivation"
    assert is_active is False, (
        "is_active stayed true — every guard in this system that asks 'is this "
        "account live' would answer yes for a closed one")


# ── being refused afterwards ───────────────────────────────────────────────
async def test_a_closed_account_is_refused_with_the_SAME_401_as_a_wrong_password(
        client, clean_db) -> None:
    """`SW-ADR-100 (1)`, unchanged by `CR-001` and load-bearing because of it.

    A closed account **keeps its email address** — the unique index on
    `lower(email)` stays total — so a distinct refusal here would tell anyone
    who can type an address both that the person existed AND that they have
    left. `ACCOUNT_CLOSED` is the tempting code and it is an enumeration oracle
    with a friendlier name.

    The two bodies are compared for **equality**, not both checked for 401: two
    different sentences behind the same status is the same oracle, one `curl`
    further away.
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert (await client.delete("/api/auth/me")).status_code == 204

    closed = await client.post("/api/auth/login", json={
        "email": made["A"]["email"], "password": made["A"]["password"]})
    wrong = await client.post("/api/auth/login", json={
        "email": made["A"]["email"], "password": "x" * 14})

    assert closed.status_code == wrong.status_code == 401
    assert closed.json() == wrong.json(), (
        "a closed account and a wrong password gave different answers — that is "
        "an account-enumeration oracle, SW-ADR-100 (1)")


async def test_a_session_already_open_elsewhere_is_refused_after_the_close(
        client, clean_db) -> None:
    """`CR-001 §2`: an in-flight session is refused on its **next** request.

    Every device, not only the one that pressed the button. The refusal arrives
    from `principal_for`, which re-reads the row per request — so it is immediate
    rather than "whenever the cookie expires", which for this system is thirty
    days.

    Either `SESSION_INVALID` or `ACCOUNT_DEACTIVATED` is correct and the test
    says so deliberately. `delete_self` revokes the session rows in the same
    transaction, and `principal_for` checks `revoked_at` **before** it reads the
    user — so the revocation usually answers first. `CR-001` names
    `ACCOUNT_DEACTIVATED` for the case where it does not. Pinning one would be
    asserting the order of two guards that are both meant to hold, and the
    person on the other end sees the same closed-account screen either way.
    """
    import httpx

    from app.main import app

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://testserver") as elsewhere:
        await _sign_in(elsewhere, made["A"])
        assert (await elsewhere.get("/api/auth/me")).status_code == 200

        assert (await client.delete("/api/auth/me")).status_code == 204

        r = await elsewhere.get("/api/auth/me")
        assert r.status_code == 401, r.text
        assert r.json()["error"]["code"] in ("ACCOUNT_DEACTIVATED", "SESSION_INVALID")


async def test_the_address_of_a_closed_account_cannot_be_registered_again(
        client, clean_db) -> None:
    """**The consequence nobody expects**, and `CR-001` says so in as many words.

    The unique index on `lower(email)` stays **total**. The alternative — a
    partial index excluding closed rows — lets a person return under the same
    address and creates two rows with one address, which every lookup in this
    system would then have to disambiguate correctly, forever.

    So the address stays taken, the answer is `409 EMAIL_TAKEN`, and the route
    back is an administrator restoring the account. The status AND the code are
    asserted: a 422 here would mean the index was made partial and the
    constraint moved into the application, which is the shape `SW-ADR-072`
    refuses because it races.
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert (await client.delete("/api/auth/me")).status_code == 204

    again = await client.post("/api/auth/register", json={
        "email": made["A"]["email"], "password": "a-brand-new-passphrase-here",
        "display_name": "Someone Else"})

    assert again.status_code == 409, again.text
    assert again.json()["error"]["code"] == "EMAIL_TAKEN"
    assert again.json()["error"]["field"] == "email"


async def test_the_last_active_administrator_cannot_close_their_account(
        client, clean_db, test_urls) -> None:
    """`CR-001 §2`: `409 CONFLICT`, `field: "is_active"` — and they stay usable.

    The same guard as demotion (`SW-ADR-098 (1)`) and as `deactivate_self`,
    because it is the same failure: a system nobody can administer, recoverable
    only by hand-written SQL. It runs BEFORE any column is touched, which is why
    the second half of this test matters — a refused close that had already
    written `deleted_at` would leave an account that is closed and still says it
    is not.
    """
    from sqlalchemy import text

    made = await seed(client, guard_database=clean_db)
    await _promote(test_urls, made["A"]["id"])
    await _sign_in(client, made["A"])

    r = await client.delete("/api/auth/me")
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "CONFLICT"
    assert r.json()["error"]["field"] == "is_active"

    # Still signed in, still an administrator, still nothing written.
    me = await client.get("/api/auth/me")
    assert me.status_code == 200, "the refused close signed them out anyway"
    assert me.json()["role"] == "admin"

    async with _owner_reading_as(test_urls, made["A"]["id"]) as c:
        row = (await c.execute(text(
            "SELECT is_active, deleted_at FROM users WHERE id = :i"),
            {"i": made["A"]["id"]})).one()
    assert row[0] is True and row[1] is None, (
        "the refused close still touched the row — the guard runs after the write")


# ── coming back ────────────────────────────────────────────────────────────
async def test_an_administrator_restores_a_closed_account_in_ONE_action(
        client, clean_db, test_urls) -> None:
    """`CR-001 §2`: `is_active: true` on a closed account **also clears
    `deleted_at`**.

    One action, not two. Two would mean an intermediate state — reactivated but
    still marked closed — that `principal_for` refuses on sight, so the
    administrator would report "I turned it back on and they still cannot sign
    in" and be entirely right.

    Proven end to end rather than at the column: the person signs in afterwards
    and their four expenses are still attached. That is the promise the settings
    copy makes to someone about to press the button.
    """
    from sqlalchemy import text

    made = await seed(client, guard_database=clean_db)
    await _promote(test_urls, made["B"]["id"])

    await _sign_in(client, made["A"])
    assert (await client.delete("/api/auth/me")).status_code == 204

    await _sign_in(client, made["B"])
    r = await client.post(f"/api/admin/users/{made['A']['id']}/active",
                          json={"is_active": True})
    assert r.status_code == 200, r.text

    async with _owner_reading_as(test_urls, made["A"]["id"]) as c:
        row = (await c.execute(text(
            "SELECT is_active, deleted_at FROM users WHERE id = :i"),
            {"i": made["A"]["id"]})).one()
    assert row[0] is True
    assert row[1] is None, (
        "deleted_at survived the restore — the account is active AND closed, "
        "which principal_for refuses on every request")

    await client.post("/api/auth/logout")
    await _sign_in(client, made["A"])
    assert (await client.get("/api/expenses")).json()["total"] == 4, (
        "restored, but their expenses did not come back with them")


# ── the two doors are different doors ──────────────────────────────────────
async def test_deactivating_and_closing_are_not_the_same_thing(client, clean_db,
                                                               test_urls) -> None:
    """**Both endpoints survive `CR-001`, and they stay distinct.**

    `POST /api/auth/deactivate` is "pause me"; `DELETE /api/auth/me` is "close
    it". A person who asks to delete their account and gets a deactivation has
    been told something untrue about what just happened, and the reverse is
    worse.

    Two people, one of each, one read — so the assertion is a COMPARISON and not
    two independent claims that could both drift the same way. The shared half
    (`is_active false`, sessions gone) is asserted too: if the two rows were
    identical in every column the endpoints would be one endpoint wearing two
    names, which is exactly what `SW-ADR-148` warned about and `CR-001` repeats.
    """
    from sqlalchemy import text

    made = await seed(client, guard_database=clean_db)

    await _sign_in(client, made["A"])
    assert (await client.post("/api/auth/deactivate")).status_code == 204

    await _sign_in(client, made["B"])
    assert (await client.delete("/api/auth/me")).status_code == 204

    async with _owner_reading_as(test_urls, made["A"]["id"]) as c:
        rows = {r[0]: (r[1], r[2]) for r in (await c.execute(text(
            "SELECT id, is_active, deleted_at FROM users ORDER BY id"))).all()}

    paused = rows[made["A"]["id"]]
    closed = rows[made["B"]["id"]]

    assert paused[0] is False and closed[0] is False, "both should be switched off"
    assert paused[1] is None, (
        "deactivating set deleted_at — /deactivate is now an alias for delete, "
        "and the settings screen offers two buttons that do one thing")
    assert closed[1] is not None, "closing did not set deleted_at"


async def test_a_closed_account_is_still_in_the_account_list_by_default(
        client, clean_db, test_urls) -> None:
    """`CR-001 §2`: the default **includes** closed accounts, and that is the
    opposite of the instinct.

    An administrator looking for someone who has left must be able to find them.
    A list that silently hides them turns "restore this account" into a support
    ticket about a person who appears never to have existed — and the restore is
    the whole reason the deletion is soft.

    `deleted` is a boolean on the row, not a timestamp (`SW-ADR-150`): the
    instant an account closed is an operational detail the list has no use for,
    and a field that does not exist cannot be leaked by a handler that forgets.
    """
    made = await seed(client, guard_database=clean_db)
    await _promote(test_urls, made["B"]["id"])

    await _sign_in(client, made["A"])
    assert (await client.delete("/api/auth/me")).status_code == 204
    await _sign_in(client, made["B"])

    everyone = (await client.get("/api/admin/users")).json()
    rows = {u["id"]: u for u in everyone["items"]}
    assert everyone["total"] == 2, "a closed account vanished from the default list"
    assert rows[made["A"]["id"]]["deleted"] is True
    assert rows[made["A"]["id"]]["is_active"] is False
    assert rows[made["B"]["id"]]["deleted"] is False, (
        "an administrator who has not left is reported as deleted")

    only_closed = (await client.get("/api/admin/users?deleted=true")).json()
    assert [u["id"] for u in only_closed["items"]] == [made["A"]["id"]]

    still_here = (await client.get("/api/admin/users?deleted=false")).json()
    assert [u["id"] for u in still_here["items"]] == [made["B"]["id"]]
