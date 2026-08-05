"""E0-S7 — THE GATE: person B is denied at the DATABASE layer.

Every other test in this repository goes through the application. These do not.
They open a connection **as the runtime role**, set `app.user_id` to person B by
hand, and issue raw SQL against person A's rows.

That distinction is the entire point. `CONSTITUTION.md` Art IV.1 requires
isolation enforced **twice** — once by the application's `WHERE user_id = …`,
and once by PostgreSQL row-level security. An API test proves layer one. Only
this file proves layer two, and layer two is what still holds if someone forgets
a predicate, adds an endpoint, or writes a report query at 2am.

`SW-ADR-078` and `SW-ADR-082` — which superseded `SW-ADR-018` — call a
controller-only check "the classic false green". This is the file that makes
that not the case here.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = pytest.mark.db


@pytest_asyncio.fixture
async def two_people(client):
    """A and B, each with one expense, created through the real API.

    Returns `(a_id, a_expense_id, b_id, b_expense_id)`. Built through the
    endpoints rather than by INSERT so the rows are exactly what the application
    would have written — seeding by INSERT would skip the very paths being
    tested (`SW-ADR-086`).
    """
    await client.post("/api/auth/register", json={
        "email": "a@spendwise.test", "password": "correct-horse-battery-staple",
        "display_name": "Person A"})
    a_id = (await client.get("/api/auth/me")).json()["id"]
    a_exp = (await client.post("/api/expenses", json={
        "amount": "1250.00", "spent_on": "2026-08-01",
        "description": "A's private lunch"})).json()["id"]
    await client.post("/api/auth/logout")

    await client.post("/api/auth/register", json={
        "email": "b@spendwise.test", "password": "correct-horse-battery-staple",
        "display_name": "Person B"})
    b_id = (await client.get("/api/auth/me")).json()["id"]
    b_exp = (await client.post("/api/expenses", json={
        "amount": "99.99", "spent_on": "2026-08-01"})).json()["id"]

    return a_id, a_exp, b_id, b_exp


@pytest_asyncio.fixture
async def as_runtime_role(clean_db):
    """A raw connection as `spendwise_app` — the role the application uses.

    Not the owner. The owner is subject to `FORCE ROW LEVEL SECURITY` too, but
    testing as the owner would prove something weaker than what production does.
    """
    engine = create_async_engine(clean_db, poolclass=None)
    async with engine.connect() as conn:
        yield conn
    await engine.dispose()


async def _as(conn, user_id: int):
    """Become that person, for this transaction. The bound-parameter form —
    `SET LOCAL` cannot take one (`SW-ADR-082`)."""
    await conn.execute(text("SELECT set_config('app.user_id', :uid, true)"),
                       {"uid": str(user_id)})


# ── E0-S7: the four denials ────────────────────────────────────────────────
async def test_b_selecting_as_row_returns_zero_rows(two_people, as_runtime_role) -> None:
    """AC2. **This is the assertion the whole product rests on.**

    Not "returns an error", not "returns a filtered view" — the row is simply
    not there. As far as person B's connection is concerned, person A's spending
    does not exist.
    """
    a_id, a_exp, b_id, _ = two_people
    conn = as_runtime_role
    async with conn.begin():
        await _as(conn, b_id)
        rows = (await conn.execute(
            text("SELECT * FROM expenses WHERE id = :i"), {"i": a_exp})).fetchall()
        assert rows == [], "person B's connection can see person A's money"


async def test_a_can_see_their_own_row(two_people, as_runtime_role) -> None:
    """The control. Without this, a policy that denies EVERYTHING would pass
    every other test in this file — a false green in the opposite direction."""
    a_id, a_exp, _, _ = two_people
    conn = as_runtime_role
    async with conn.begin():
        await _as(conn, a_id)
        row = (await conn.execute(
            text("SELECT amount_paise FROM expenses WHERE id = :i"), {"i": a_exp})).one()
        assert row[0] == 125000


async def test_b_updating_as_row_affects_zero_rows(two_people, as_runtime_role) -> None:
    """AC3. A read-only policy would let this through — which is exactly why
    every policy carries `FOR ALL` with both `USING` and `WITH CHECK`."""
    a_id, a_exp, b_id, _ = two_people
    conn = as_runtime_role
    async with conn.begin():
        await _as(conn, b_id)
        r = await conn.execute(
            text("UPDATE expenses SET amount_paise = 1 WHERE id = :i"), {"i": a_exp})
        assert r.rowcount == 0

    async with conn.begin():
        await _as(conn, a_id)
        still = (await conn.execute(
            text("SELECT amount_paise FROM expenses WHERE id = :i"), {"i": a_exp})).one()
        assert still[0] == 125000, "person B silently rewrote person A's amount"


async def test_b_deleting_as_row_affects_zero_rows(two_people, as_runtime_role) -> None:
    """AC4. Deletion is the one that cannot be undone, so it gets its own case
    rather than being assumed to follow from UPDATE."""
    a_id, a_exp, b_id, _ = two_people
    conn = as_runtime_role
    async with conn.begin():
        await _as(conn, b_id)
        r = await conn.execute(text("DELETE FROM expenses WHERE id = :i"), {"i": a_exp})
        assert r.rowcount == 0

    async with conn.begin():
        await _as(conn, a_id)
        n = (await conn.execute(
            text("SELECT count(*) FROM expenses WHERE id = :i"), {"i": a_exp})).scalar()
        assert n == 1, "person B deleted person A's expense"


async def test_b_cannot_insert_a_row_stamped_with_as_id(two_people, as_runtime_role) -> None:
    """`NEG-X-18`. The `WITH CHECK` half.

    This is the backstop for the application forgetting to discard a forged
    `user_id`. Even if every layer above failed, the database refuses to write a
    row under someone else's name.
    """
    a_id, _, b_id, _ = two_people
    conn = as_runtime_role
    with pytest.raises(DBAPIError) as exc:
        async with conn.begin():
            await _as(conn, b_id)
            await conn.execute(text(
                "INSERT INTO expenses (user_id, amount_paise, currency, spent_on) "
                "VALUES (:u, 100, 'INR', DATE '2026-08-01')"), {"u": a_id})
    assert "row-level security" in str(exc.value).lower()


async def test_with_no_identity_set_nothing_is_visible(two_people, as_runtime_role) -> None:
    """Fail CLOSED. A connection that forgot `set_config` sees nothing at all —
    it does not see everything.

    `current_setting('app.user_id', true)` is NULL, so the predicate is NULL,
    so no row qualifies. This is why the missing-GUC failure mode is an empty
    dashboard rather than a data breach (`GOTCHAS`).
    """
    conn = as_runtime_role
    async with conn.begin():
        n = (await conn.execute(text("SELECT count(*) FROM expenses"))).scalar()
        assert n == 0, "a connection with no identity could read rows"


async def test_the_runtime_role_cannot_disable_the_policy(as_runtime_role) -> None:
    """The guarantee has to survive the role that runs under it.

    An owner can `ALTER TABLE … NO FORCE ROW LEVEL SECURITY`. The runtime role
    owns no table, which is precisely why `SW-ADR-081` splits them — and why the
    boot assertion checks ownership rather than trusting it.
    """
    conn = as_runtime_role
    with pytest.raises(DBAPIError) as exc:
        async with conn.begin():
            await conn.execute(text("ALTER TABLE expenses NO FORCE ROW LEVEL SECURITY"))
    msg = str(exc.value).lower()
    assert "must be owner" in msg or "permission denied" in msg


async def test_the_admin_guc_changes_nothing(two_people, as_runtime_role) -> None:
    """`NEG-X-21`. Setting `app.is_admin` must not widen a single read.

    The superseded `SW-ADR-077` created a permissive policy keyed on this GUC.
    Permissive policies are OR'd, so it returned every column of every row to
    any connection that set it. `SW-ADR-129` removed it; this asserts it has not
    come back.
    """
    a_id, a_exp, b_id, _ = two_people
    conn = as_runtime_role
    async with conn.begin():
        await _as(conn, b_id)
        await conn.execute(text("SELECT set_config('app.is_admin', 'true', true)"))
        rows = (await conn.execute(
            text("SELECT * FROM expenses WHERE id = :i"), {"i": a_exp})).fetchall()
        assert rows == [], "app.is_admin widened a read — SW-ADR-077's hole is back"
