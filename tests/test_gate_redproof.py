"""E0-S8 — RED-PROOF the gate.

`CONSTITUTION.md` Art IV.4: **a check that has never been observed failing
proves nothing.** `test_gate_isolation.py` passes — but so would a test against
a table with no rows, a typo'd id, or a query that silently errors into an empty
list. Passing is not evidence until failing has been seen.

So this file breaks the guarantee on purpose:

    1. assert person B is denied                    (green)
    2. ALTER TABLE expenses DISABLE ROW LEVEL SECURITY, as the OWNER
    3. confirm the catalog actually changed         — the change is real
    4. re-run the same assertion and watch it FAIL  (RED — person A's row comes back)
    5. revert
    6. confirm the catalog changed back             — the revert is real
    7. re-run and watch it pass again               (green)

Steps 3 and 6 exist because "I ran an ALTER" is not the same as "the setting
changed". Both are read back from `pg_class`.

**The break is `DISABLE`, not `NO FORCE`, and the difference is the whole
lesson.** The first version of this file used `NO FORCE` — and the test REFUSED
TO GO RED, which is how the mistake surfaced. `FORCE` governs only whether the
TABLE OWNER is subject to its own policies. `spendwise_app` does not own the
table, so RLS applied to it either way and `NO FORCE` changed nothing it could
observe.

Both settings matter, for different threats:

* **`ENABLE`/`DISABLE`** is what stands between person B and person A. That is
  what the gate proves, so that is what gets broken here.
* **`FORCE`** is what stands between a migration run by the owner and silently
  affecting zero rows. It is asserted at boot and by the guard at the foot of
  this file.

A red-proof that breaks the wrong setting proves nothing — and would have
reported a passing gate forever.

**Only ever against `spendwise_test`**, and the revert is in a `finally` — a
half-reverted test database is a guarantee silently switched off for every run
afterwards, which is worse than the test not existing.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

pytestmark = [pytest.mark.db, pytest.mark.gate]

TABLE = "expenses"


@pytest_asyncio.fixture
async def owner_engine(test_urls):
    """Only the OWNER can toggle `FORCE ROW LEVEL SECURITY` — which is itself
    the point of `SW-ADR-081` splitting the roles."""
    if test_urls is None:
        pytest.skip("no database configured")
    _, owner_url = test_urls
    if "/spendwise_test" not in owner_url:
        pytest.skip("refusing to red-proof anything but spendwise_test")
    engine = create_async_engine(owner_url, poolclass=None)
    yield engine
    await engine.dispose()


async def _force_rls(engine) -> bool:
    async with engine.connect() as c:
        return bool(await c.scalar(
            text("SELECT relforcerowsecurity FROM pg_class WHERE relname = :t"),
            {"t": TABLE}))


async def _rls_enabled(engine) -> bool:
    async with engine.connect() as c:
        return bool(await c.scalar(
            text("SELECT relrowsecurity FROM pg_class WHERE relname = :t"), {"t": TABLE}))


async def _set_rls(engine, on: bool) -> None:
    """ENABLE/DISABLE — what the RUNTIME role can observe. Re-enabling also
    re-asserts FORCE, because DISABLE leaves FORCE set but inert, and a revert
    that restores only half the state is not a revert."""
    async with engine.begin() as c:
        if on:
            await c.execute(text(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY"))
            await c.execute(text(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY"))
        else:
            await c.execute(text(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY"))


async def _b_can_see_as_row(runtime_url, a_expense_id: int, b_id: int) -> bool:
    """The assertion under test, isolated so the same code runs in all three
    passes. If it returned different SQL each time, the red would prove nothing
    about the green."""
    engine = create_async_engine(runtime_url, poolclass=None)
    try:
        async with engine.connect() as conn, conn.begin():
            await conn.execute(text("SELECT set_config('app.user_id', :u, true)"),
                               {"u": str(b_id)})
            rows = (await conn.execute(
                text("SELECT * FROM expenses WHERE id = :i"),
                {"i": a_expense_id})).fetchall()
            return len(rows) > 0
    finally:
        await engine.dispose()


async def test_the_denial_is_observed_going_red_and_back(client, clean_db,
                                                         owner_engine) -> None:
    # Two people with one expense each, through the real API.
    await client.post("/api/auth/register", json={
        "email": "a@spendwise.test", "password": "correct-horse-battery-staple",
        "display_name": "Person A"})
    a_exp = (await client.post("/api/expenses", json={
        "amount": "1250.00", "spent_on": "2026-08-01"})).json()["id"]
    await client.post("/api/auth/logout")

    await client.post("/api/auth/register", json={
        "email": "b@spendwise.test", "password": "correct-horse-battery-staple",
        "display_name": "Person B"})
    b_id = (await client.get("/api/auth/me")).json()["id"]

    steps: list[str] = []
    try:
        # 1 — green
        assert await _rls_enabled(owner_engine) is True
        assert await _force_rls(owner_engine) is True
        assert not await _b_can_see_as_row(clean_db, a_exp, b_id)
        steps.append("green: B denied with row-level security on")

        # 2 + 3 — break it, and confirm the break is REAL
        await _set_rls(owner_engine, False)
        assert await _rls_enabled(owner_engine) is False, (
            "the ALTER reported success but pg_class still says RLS is enabled — "
            "the red-proof would have proved nothing")
        steps.append("catalog confirms ROW LEVEL SECURITY is DISABLED")

        # 4 — RED. The row comes back. This is the observation that makes step 1
        #     mean something: it proves the denial is produced by THE POLICY and
        #     not by an empty table, a wrong id, or a query erroring into [].
        leaked = await _b_can_see_as_row(clean_db, a_exp, b_id)
        steps.append(f"red: B {'CAN' if leaked else 'still cannot'} see A's row")
        assert leaked, (
            "with ROW LEVEL SECURITY disabled, person B STILL could not "
            "see person A's row. The denial in test_gate_isolation is therefore "
            "not being produced by the policy — something else is hiding the "
            "row, and the isolation guarantee is unproven")

    finally:
        # 5 + 6 — revert, and confirm the revert is REAL. In `finally` because a
        # half-reverted test database silently switches the guarantee off for
        # every run afterwards.
        await _set_rls(owner_engine, True)
        assert await _rls_enabled(owner_engine) is True, (
            "FAILED TO REVERT — spendwise_test now has ROW LEVEL SECURITY "
            "DISABLED on expenses. Fix before trusting any later run.")
        assert await _force_rls(owner_engine) is True, "FORCE was not restored"
        steps.append("reverted, catalog confirms RLS enabled and FORCEd")

    # 7 — green again, with the same code that went red
    assert not await _b_can_see_as_row(clean_db, a_exp, b_id)
    steps.append("green again after revert")

    assert len(steps) == 5, steps


async def test_force_is_on_for_every_protected_table_afterwards(owner_engine) -> None:
    """A guard for the whole suite. If a red-proof ever aborts between breaking
    and reverting, this is the test that says so out loud instead of letting
    every later run pass for the wrong reason."""
    async with owner_engine.connect() as c:
        rows = (await c.execute(text(
            "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class "
            "WHERE relname IN ('expenses','categories','sessions') ORDER BY relname"
        ))).fetchall()
    assert [r[0] for r in rows] == ["categories", "expenses", "sessions"]
    not_enabled = [r[0] for r in rows if not r[1]]
    not_forced = [r[0] for r in rows if not r[2]]
    assert not not_enabled, (
        f"ROW LEVEL SECURITY is DISABLED for {not_enabled} — a red-proof did not "
        f"revert, and every isolation test after it passes for no reason")
    assert not not_forced, f"FORCE ROW LEVEL SECURITY is OFF for {not_forced}"
