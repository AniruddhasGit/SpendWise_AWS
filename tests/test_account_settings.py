"""The settings a person owns — `SW-ADR-148`.

Change your name, change your password, take your data, leave.

**This file covers DEACTIVATION.** `SW-ADR-107` previously ruled that user
deletion did not exist in v1 — *"Deleting a person's financial history is the
clearest one-way door in the register."* It has since been superseded by
`SW-ADR-150`, and closing an account now exists in its soft form; that path is
covered by `test_soft_delete.py`.

Deactivation did not go away when deletion arrived, and the two remain
genuinely different: **pause me** and **close it**. `/api/auth/export` is the
counterweight to both — nothing is erased either way, and you can always take
the record with you.
"""
from __future__ import annotations

import pytest

from tests.seed import seed

pytestmark = [pytest.mark.db]


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


# ── profile ────────────────────────────────────────────────────────────────
async def test_a_person_can_change_their_display_name(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.patch("/api/auth/me", json={"display_name": "Asha Nair"})
    assert r.status_code == 200, r.text
    assert r.json()["display_name"] == "Asha Nair"
    assert (await client.get("/api/auth/me")).json()["display_name"] == "Asha Nair"


async def test_the_email_cannot_be_changed(client, clean_db) -> None:
    """Absent from the model deliberately: it is the identity the unique index
    is built on, and changing it is an account-takeover vector when nothing
    verifies the new address — `SW-ADR-012` records that there is no email in
    this stack to verify with.

    `extra="ignore"`, so the key is DISCARDED rather than rejected — the same
    posture `SW-ADR-130` takes for a forged `user_id`.
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.patch("/api/auth/me", json={"email": "someone-else@x.test"})
    assert r.status_code == 200
    assert r.json()["email"] == made["A"]["email"]


@pytest.mark.parametrize("name", ["", "x" * 101])
async def test_a_bad_display_name_is_422(client, clean_db, name) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch("/api/auth/me", json={"display_name": name})
    assert r.status_code == 422
    assert r.json()["error"]["field"] == "display_name"


# ── password ───────────────────────────────────────────────────────────────
async def test_changing_a_password_keeps_this_session_and_ends_the_others(
        client, clean_db) -> None:
    """Signing someone out of the browser they are standing in punishes the
    action this exists to encourage. Every OTHER session goes, because
    "change my password" is what a person does when they suspect one of them
    is not theirs."""
    import httpx

    from app.main import app

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://testserver") as other:
        await _sign_in(other, made["A"])
        assert (await other.get("/api/auth/me")).status_code == 200

        new = "a-completely-different-passphrase"
        r = await client.post("/api/auth/password", json={
            "current_password": made["A"]["password"], "new_password": new})
        assert r.status_code == 200, r.text
        assert r.json()["signed_out_elsewhere"] >= 1

        # This session survives.
        assert (await client.get("/api/auth/me")).status_code == 200
        # The other does not.
        assert (await other.get("/api/auth/me")).status_code == 401

    await client.post("/api/auth/logout")
    assert (await client.post("/api/auth/login", json={
        "email": made["A"]["email"], "password": new})).status_code == 200


async def test_the_wrong_current_password_is_refused(client, clean_db) -> None:
    """Requiring the current password is what stops a stolen SESSION becoming a
    stolen ACCOUNT — without it, anyone holding a live cookie locks the owner
    out."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.post("/api/auth/password", json={
        "current_password": "not-the-right-one", "new_password": "x" * 20})
    assert r.status_code == 401

    # And the real one still works.
    await client.post("/api/auth/logout")
    await _sign_in(client, made["A"])


@pytest.mark.parametrize("bad", ["short", "x" * 73])
async def test_a_new_password_outside_12_to_72_bytes_is_422(client, clean_db,
                                                            bad) -> None:
    """The upper bound is bcrypt's: it silently ignores bytes past 72, so two
    long passwords sharing a 72-byte prefix would be one password and nobody
    would be told."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.post("/api/auth/password", json={
        "current_password": made["A"]["password"], "new_password": bad})
    assert r.status_code == 422
    assert r.json()["error"]["field"] == "password"


# ── export ─────────────────────────────────────────────────────────────────
async def test_export_returns_this_account_and_only_this_account(client,
                                                                 clean_db) -> None:
    """The counterweight to there being no deletion. Under the same row-level
    security as every other request, so it could not return anyone else's rows
    even if the query were wrong."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])

    r = await client.get("/api/auth/export")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["account"]["email"] == made["B"]["email"]
    assert len(body["categories"]) == 8
    assert len(body["expenses"]) == 2
    assert sum(e["amount_paise"] for e in body["expenses"]) == 125000

    # Not one paisa of person A's.
    assert "379049" not in r.text
    assert "2100.00" not in r.text
    assert all(e["user_id"] == made["B"]["id"] for e in body["expenses"])


# ── deactivation ───────────────────────────────────────────────────────────
async def test_deactivating_ends_the_session_and_refuses_sign_in(client,
                                                                 clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.post("/api/auth/deactivate")
    assert r.status_code == 204

    assert (await client.get("/api/auth/me")).status_code == 401
    assert (await client.post("/api/auth/login", json={
        "email": made["A"]["email"], "password": made["A"]["password"]})).status_code == 401


async def test_deactivating_keeps_every_row(client, clean_db, test_urls) -> None:
    """Deactivation keeps everything, and it is still not the delete button.

    `SW-ADR-107` — superseded by `SW-ADR-150` — is why this was once the ONLY
    way out. It no longer is, and the assertion did not change: the account is
    switched off; the expenses, the categories and the person record are all
    still there, and an administrator can switch it back on.

    What `SW-ADR-150` added beside it is `deleted_at`, and the test that closing
    is distinct from pausing lives in `test_soft_delete.py`.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    await client.post("/api/auth/deactivate")

    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.connect() as c, c.begin():
        await c.execute(text("SELECT set_config('app.user_id', :u, true)"),
                        {"u": str(made["A"]["id"])})
        expenses = (await c.execute(text("SELECT count(*) FROM expenses"))).scalar()
        cats = (await c.execute(text("SELECT count(*) FROM categories"))).scalar()
        active = (await c.execute(text("SELECT is_active FROM users WHERE id = :i"),
                                  {"i": made["A"]["id"]})).scalar()
    await e.dispose()

    assert expenses == 4, "deactivation destroyed the money"
    assert cats == 8
    assert active is False


async def test_an_admin_can_reactivate_a_deactivated_person(client, clean_db,
                                                            test_urls) -> None:
    """Which is the whole argument for deactivation over deletion: it is
    reversible, and a person who leaves in anger on Tuesday can come back on
    Thursday with their record intact."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    made = await seed(client, guard_database=clean_db)
    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("UPDATE users SET role='admin' WHERE id=:i"),
                        {"i": made["B"]["id"]})
    await e.dispose()

    await _sign_in(client, made["A"])
    await client.post("/api/auth/deactivate")

    await _sign_in(client, made["B"])
    r = await client.post(f"/api/admin/users/{made['A']['id']}/active",
                          json={"is_active": True})
    assert r.status_code == 200, r.text
    await client.post("/api/auth/logout")

    await _sign_in(client, made["A"])
    assert (await client.get("/api/expenses")).json()["total"] == 4


async def test_the_last_active_admin_cannot_deactivate_themselves(
        client, clean_db, test_urls) -> None:
    """Same guard as demotion (`SW-ADR-098 (1)`): any action that would leave
    zero active administrators is refused, because recovery from that state is
    hand-written SQL."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    made = await seed(client, guard_database=clean_db)
    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("UPDATE users SET role='admin' WHERE id=:i"),
                        {"i": made["A"]["id"]})
    await e.dispose()

    await _sign_in(client, made["A"])
    r = await client.post("/api/auth/deactivate")
    assert r.status_code == 409, r.text
    assert (await client.get("/api/auth/me")).status_code == 200


async def test_every_settings_route_needs_a_session(client, clean_db) -> None:
    for method, path, body in (
        ("patch", "/api/auth/me", {"display_name": "x"}),
        ("post", "/api/auth/password", {"current_password": "a", "new_password": "b"}),
        ("post", "/api/auth/deactivate", None),
        ("get", "/api/auth/export", None),
    ):
        r = await client.request(method.upper(), path,
                                 **({"json": body} if body else {}))
        assert r.status_code == 401, f"{method} {path} -> {r.status_code}"
