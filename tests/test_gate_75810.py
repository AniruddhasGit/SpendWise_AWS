"""E0-S4 and E0-S9 — THE GATE: the business rule computes 75810.

The never-waivable one (`CONSTITUTION` Art IX.4). Everything else in M0 exists
so that this can be trusted.

`test_gate_arithmetic.py` already proves the maths, with no database. This
proves the whole path: seeded through the real endpoints, read back through the
real endpoint, computed by application code from rows PostgreSQL returned.

Two failures, deliberately separated — right rows, and right maths on them. This
file is where they meet.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.seed import expenses_for, people, seed

pytestmark = [pytest.mark.db, pytest.mark.gate]

REPO = Path(__file__).resolve().parents[1]
EXPECTED = json.loads(
    (REPO / "docs" / "06 DataModel" / "seed" / "expected_summary.json").read_text("utf-8"))
GATE = json.loads(
    (REPO / "docs" / "03 PRD" / "api" / "contract.json").read_text("utf-8"))["gate"]

QUERY = f"/api/expenses/summary?from={EXPECTED['from']}&to={EXPECTED['to']}"

# `SW-ADR-039` freezes the gate to 2026-08-05. 379049 / 5 = 75810 holds ON THAT
# DAY and no other: `days_elapsed` is min(to, today) - from + 1, so the divisor
# grows by one every midnight until the month ends.
GATE_DAY = GATE["as_of"]        # stated in the contract, never typed here


@pytest.fixture(autouse=True)
def _frozen_to_the_gate_day(monkeypatch):
    """Pin `today`. **Autouse, so it runs before `client`** — which clears the
    settings cache and re-imports the app, and would otherwise bake in the real
    date.

    This was missing until 2026-08-06, when the wall clock rolled over and four
    gate assertions went red at midnight. They had passed for one day. Every
    other reading of them — in CI, on another machine, tomorrow — would have
    been a failure with no code change behind it, which is precisely the shape
    `CV-14` added `APP_TODAY_OVERRIDE` to prevent. The browser tests had it from
    the start; the in-process ones inherited the system clock and nobody
    noticed, because the day they were written was the day they were pinned to.
    """
    monkeypatch.setenv("APP_TODAY_OVERRIDE", GATE_DAY)


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


# ── E0-S4: the seed ────────────────────────────────────────────────────────
async def test_the_seed_creates_exactly_two_people_with_eight_categories(client,
                                                                         clean_db) -> None:
    """AC1. **Two**, not three — `SRC-001` ERRATUM E-6 and Art IX.4.

    The bootstrap admin is an address nobody registers; setting
    `BOOTSTRAP_ADMIN_EMAIL` is what `P-ACC-02` requires, and registering a third
    account is not.
    """
    made = await seed(client, guard_database=clean_db)
    assert set(made) == {"A", "B"}
    assert len(people()) == 2


async def test_person_a_has_exactly_the_four_amounts(client, clean_db) -> None:
    """AC2. The four of `P-UND-02`, on the stated dates."""
    made = await seed(client, guard_database=clean_db)
    got = sorted(e["amount_paise"] for e in made["A"]["expenses"])
    assert got == sorted(e["amount_paise"] for e in expenses_for("A"))
    assert got == [9999, 34050, 125000, 210000]


async def test_the_seed_refuses_any_database_but_the_test_one(client) -> None:
    """AC5. It creates accounts with KNOWN PASSWORDS. That is only ever safe
    against a database which is dropped and rebuilt."""
    with pytest.raises(RuntimeError, match="refusing to seed"):
        await seed(client, guard_database="postgresql://x/spendwise?ssl=require")


async def test_seeding_twice_from_empty_gives_identical_counts(client, clean_db,
                                                               test_urls) -> None:
    """AC3, printed and compared. A seed that is not reproducible makes every
    number downstream of it an anecdote."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    runtime_url, owner_url = test_urls

    async def counts() -> dict[str, int]:
        """Counted per person, with `app.user_id` set for each.

        FORCE ROW LEVEL SECURITY applies to the OWNER TOO — that is the whole
        point of FORCE. A plain `SELECT count(*) FROM expenses` on this
        connection returns **0**, not because the rows are missing but because
        the owner is subject to its own policies. The first version of this test
        did exactly that and reported an empty database.

        `users` is outside RLS (`SW-ADR-097`) so it counts directly.
        """
        e = create_async_engine(owner_url, poolclass=None)
        try:
            async with e.connect() as c, c.begin():
                out = {"users": (await c.execute(
                    text("SELECT count(*) FROM users"))).scalar()}
            for table in ("categories", "expenses"):
                total = 0
                for p in people():
                    # A FRESH transaction per person: set_config(..., true) is
                    # transaction-local, so reusing one would carry the previous
                    # person's identity into the next count.
                    async with e.connect() as c, c.begin():
                        await c.execute(
                            text("SELECT set_config('app.user_id', :u, true)"),
                            {"u": str(p["registration_order"])})
                        total += (await c.execute(
                            text(f"SELECT count(*) FROM {table}"))).scalar()
                out[table] = total
            return out
        finally:
            await e.dispose()

    await seed(client, guard_database=clean_db)
    first = await counts()

    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("TRUNCATE users, categories, expenses, sessions, "
                             "password_resets, admin_audit_log, app_meta "
                             "RESTART IDENTITY CASCADE"))
    await e.dispose()

    await seed(client, guard_database=clean_db)
    second = await counts()

    print(f"\n  first  seed: {first}\n  second seed: {second}")
    assert first == second == {"users": 2, "categories": 16, "expenses": 6}


# ── E0-S9: THE GATE ────────────────────────────────────────────────────────
async def test_the_daily_average_is_75810(client, clean_db) -> None:
    """**AC1. The never-waivable assertion.**

    Seeded through the real endpoints, read back through the real endpoint,
    computed by application code from rows PostgreSQL returned under row-level
    security. Not a fixture asserting on itself.
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    s = (await client.get(QUERY)).json()
    assert s["daily_average_paise"] == 75810
    assert s["daily_average_paise"] != 75809, "truncated instead of rounding half-up"
    assert s["daily_average_paise"] != 94762, "divided by the row count, not days elapsed"


async def test_total_and_count(client, clean_db) -> None:
    """AC2."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    s = (await client.get(QUERY)).json()
    assert s["total_paise"] == 379049
    assert s["count"] == 4
    assert s["days_elapsed"] == 5, "the divisor is DAYS, not rows"


async def test_the_whole_payload_equals_the_expected_one(client, clean_db) -> None:
    """The strongest form of the gate: byte-for-byte against
    `expected_summary.json`, which is generated from the contract.

    Headline, four category buckets with their colours and percentages, and all
    31 day rows including the 27 with no spending.
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    s = (await client.get(QUERY)).json()

    for field in ("from", "to", "total_paise", "total", "count", "days_elapsed",
                  "daily_average_paise", "daily_average"):
        assert s[field] == EXPECTED[field], f"{field}: {s[field]!r} != {EXPECTED[field]!r}"

    assert s["by_category"] == EXPECTED["by_category"]
    assert s["by_day"] == EXPECTED["by_day"]
    assert len(s["by_day"]) == 31


async def test_the_value_is_computed_from_the_database_not_a_fixture(client, clean_db,
                                                                     test_urls) -> None:
    """AC3, and the one that separates "the app computed it" from "a fixture
    asserted on itself".

    Change a seeded amount **in the database**, re-request, and watch the
    average move. A hard-coded 75810 anywhere in the stack fails here.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    before = (await client.get(QUERY)).json()["daily_average_paise"]
    assert before == 75810

    target = made["A"]["expenses"][0]["id"]
    a_id = made["A"]["id"]
    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        # The identity is required even as the OWNER. FORCE ROW LEVEL SECURITY
        # subjects the owner to its own policies, so without this the UPDATE
        # matches zero rows and REPORTS SUCCESS — the silent failure FORCE
        # exists to make visible, and the reason `SW-ADR-081` warns that a data
        # migration by the owner needs to say what identity it is acting as.
        await c.execute(text("SELECT set_config('app.user_id', :u, true)"),
                        {"u": str(a_id)})
        r = await c.execute(text("UPDATE expenses SET amount_paise = amount_paise + 100000 "
                                 "WHERE id = :i"), {"i": target})
        assert r.rowcount == 1, "the UPDATE matched no row — is app.user_id set?"
    await e.dispose()

    after = (await client.get(QUERY)).json()
    assert after["total_paise"] == 479049
    assert after["daily_average_paise"] == 95810, (
        "the average did not follow the database — something is returning a "
        "constant rather than computing from rows")
    assert after["daily_average_paise"] != before


async def test_the_breakdown_sums_to_the_headline(client, clean_db) -> None:
    """AC4. `P-UND-05`'s invariant, on real rows."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    s = (await client.get(QUERY)).json()
    assert sum(b["total_paise"] for b in s["by_category"]) == s["total_paise"]
    assert sum(b["percent"] for b in s["by_category"]) == 100


async def test_person_b_gets_their_own_much_smaller_number(client, clean_db) -> None:
    """The gate's other half. B is seeded too, and B's summary must never carry
    a paisa of A's — the whole product, in one assertion."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])
    s = (await client.get(QUERY)).json()

    b_total = sum(e["amount_paise"] for e in expenses_for("B"))
    assert s["total_paise"] == b_total == 125000
    assert s["count"] == 2
    assert s["total_paise"] != 379049, "person B's summary contains person A's money"
