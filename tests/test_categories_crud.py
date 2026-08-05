"""M2 — categories list / create / rename / recolour / delete.

The one that carries weight is **delete**. `SRC-001 §7.2` says deleting a
category NULLS its expenses and never deletes them, and the composite foreign
key is `ON DELETE NO ACTION` precisely so a careless implementation gets an
error rather than a cascade. This file proves the money survives the label.
"""
from __future__ import annotations

import pytest

from tests.seed import expenses_for, seed

pytestmark = [pytest.mark.db]


def colour_of(name: str) -> str:
    """Read from the contract, never transcribed. The first version of this file
    typed Groceries' colour from memory and got a different green."""
    from app.modules.categories.service import seeded_categories
    return dict(seeded_categories())[name]


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


# ── list ───────────────────────────────────────────────────────────────────
async def test_a_new_account_lists_exactly_the_eight_seeded_categories(client,
                                                                       clean_db) -> None:
    """`P-REC-05`. Eight, in creation order, with the ruled colours."""
    from app.modules.categories.service import seeded_categories

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.get("/api/categories")
    assert r.status_code == 200, r.text
    got = r.json()
    assert [(c["name"], c["color"]) for c in got] == seeded_categories()
    assert all(c["user_id"] == made["A"]["id"] for c in got)


async def test_the_list_is_only_your_own(client, clean_db) -> None:
    """Isolation, at the layer a person can see. B's list must not contain a
    single one of A's ids — and A's are 1-8, so this is checkable exactly."""
    made = await seed(client, guard_database=clean_db)

    await _sign_in(client, made["A"])
    a_ids = {c["id"] for c in (await client.get("/api/categories")).json()}
    await client.post("/api/auth/logout")

    await _sign_in(client, made["B"])
    b_ids = {c["id"] for c in (await client.get("/api/categories")).json()}

    assert a_ids == set(range(1, 9))
    assert b_ids == set(range(9, 17))
    assert a_ids.isdisjoint(b_ids)


async def test_listing_without_a_session_is_401(client, clean_db) -> None:
    r = await client.get("/api/categories")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


# ── create ─────────────────────────────────────────────────────────────────
async def test_create_returns_201_and_the_row(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.post("/api/categories", json={"name": "Books", "color": "#3d5a80"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Books"
    assert body["color"] == "#3d5a80"
    assert body["user_id"] == made["A"]["id"]
    assert body["id"] > 16
    assert len((await client.get("/api/categories")).json()) == 9


async def test_a_duplicate_name_is_409_conflict_case_insensitively(client,
                                                                   clean_db) -> None:
    """`SW-ADR-033`. Enforced by the unique index on `(user_id, lower(name))`,
    not a pre-read — a pre-read races two concurrent requests."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.post("/api/categories", json={"name": "gRoCeRiEs", "color": "#3d5a80"})
    assert r.status_code == 409, r.text
    err = r.json()["error"]
    assert err["code"] == "CONFLICT"
    assert err["field"] == "name"
    assert err["message"] == "That already exists."


async def test_the_same_name_as_someone_else_is_allowed(client, clean_db) -> None:
    """Uniqueness is PER PERSON. Two people both having "Groceries" is the
    normal case, and a global unique index would have made it impossible."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])
    r = await client.post("/api/categories", json={"name": "Groceries II", "color": "#3d5a80"})
    assert r.status_code == 201, r.text


@pytest.mark.parametrize(("body", "field"), [
    ({"color": "#3d5a80"}, "name"),
    ({"name": "Books"}, "color"),
    ({"name": "", "color": "#3d5a80"}, "name"),
    ({"name": "x" * 51, "color": "#3d5a80"}, "name"),
    ({"name": "Books", "color": "red"}, "color"),
    ({"name": "Books", "color": "#3D5A80"}, "color"),
    ({"name": "Books", "color": "#3d5a8"}, "color"),
])
async def test_create_rejects_bad_input(client, clean_db, body, field) -> None:
    """Uppercase hex is refused too: the design system's contrast figures were
    computed against lowercase literals, and two spellings of one colour makes
    "is this colour already used" an unanswerable question."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.post("/api/categories", json=body)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["field"] == field


# ── rename and recolour ────────────────────────────────────────────────────
async def test_rename(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch("/api/categories/1", json={"name": "Food"})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Food"
    assert r.json()["color"] == colour_of("Groceries"), "recoloured while renaming"


async def test_recolour(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch("/api/categories/1", json={"color": "#3d5a80"})
    assert r.status_code == 200, r.text
    assert r.json()["color"] == "#3d5a80"
    assert r.json()["name"] == "Groceries", "renamed while recolouring"


async def test_an_empty_patch_is_422_naming_body(client, clean_db) -> None:
    """`CategoryUpdate`'s note, verbatim: at least one must be present."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch("/api/categories/1", json={})
    assert r.status_code == 422, r.text
    assert r.json()["error"]["field"] == "body"


async def test_renaming_someone_elses_category_is_404_not_403(client, clean_db) -> None:
    """`P-PRV-03`. A 403 would confirm the row exists — which is the fact being
    withheld. Not-yours and not-found are the same refusal."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])

    r = await client.patch("/api/categories/1", json={"name": "Mine now"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"

    missing = await client.patch("/api/categories/9999", json={"name": "x"})
    assert missing.status_code == 404
    assert missing.json() == r.json(), "not-yours and not-found gave different answers"


async def test_renaming_onto_an_existing_name_is_409(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch("/api/categories/1", json={"name": "Transport"})
    assert r.status_code == 409, r.text
    assert r.json()["error"]["field"] == "name"


async def test_a_conflict_leaves_the_row_untouched(client, clean_db) -> None:
    """The SAVEPOINT's job. A failed rename must not half-apply, and must not
    poison the request transaction so the next read 500s."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert (await client.patch("/api/categories/1",
                               json={"name": "Transport"})).status_code == 409

    still = await client.get("/api/categories")
    assert still.status_code == 200, "the transaction was left aborted"
    assert [c for c in still.json() if c["id"] == 1][0]["name"] == "Groceries"


# ── delete: the one that matters ───────────────────────────────────────────
async def test_delete_nulls_the_expenses_and_never_deletes_them(client,
                                                                clean_db) -> None:
    """**`SRC-001 §7.2`.** The money is the record; the label is a convenience.

    A's first expense is 2100.00 in Groceries (id 1). After deleting Groceries
    the expense must still exist, still be 210000 paise, and have no category.
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    in_groceries = [e for e in made["A"]["expenses"] if e["category_id"] == 1]
    assert in_groceries, "the fixture no longer puts anything in category 1"
    before_total = sum(e["amount_paise"] for e in expenses_for("A"))

    r = await client.delete("/api/categories/1")
    assert r.status_code == 204, r.text

    for e in in_groceries:
        kept = await client.get(f"/api/expenses/{e['id']}")
        assert kept.status_code == 200, "the expense went with the category"
        assert kept.json()["amount_paise"] == e["amount_paise"]
        assert kept.json()["category_id"] is None
        assert kept.json()["category_name"] is None

    s = (await client.get("/api/expenses/summary?from=2026-08-01&to=2026-08-31")).json()
    assert s["total_paise"] == before_total, "deleting a label changed the money"


async def test_the_deleted_category_is_gone_from_the_list(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert (await client.delete("/api/categories/2")).status_code == 204
    ids = {c["id"] for c in (await client.get("/api/categories")).json()}
    assert ids == set(range(1, 9)) - {2}


async def test_deleting_someone_elses_category_is_404(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])
    assert (await client.delete("/api/categories/1")).status_code == 404

    # And A's category is still there, which is the assertion that would catch
    # a 404 returned AFTER the delete had already happened.
    await client.post("/api/auth/logout")
    await _sign_in(client, made["A"])
    assert 1 in {c["id"] for c in (await client.get("/api/categories")).json()}


async def test_deleting_twice_is_404_the_second_time(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    assert (await client.delete("/api/categories/2")).status_code == 204
    assert (await client.delete("/api/categories/2")).status_code == 404


async def test_deleting_an_empty_category_works(client, clean_db) -> None:
    """No expenses to null. The nulling step must handle zero rows without
    reporting a problem — the common case for a category made by mistake."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    new = (await client.post("/api/categories",
                             json={"name": "Books", "color": "#3d5a80"})).json()
    assert (await client.delete(f"/api/categories/{new['id']}")).status_code == 204


async def test_the_summary_moves_the_money_to_uncategorised(client, clean_db) -> None:
    """After the delete, the total is unchanged and the orphaned money appears
    under the `Uncategorised` bucket — which is where `SW-ADR-141 D` says a
    null category_id is labelled, and the only place it is."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    q = "/api/expenses/summary?from=2026-08-01&to=2026-08-31"
    before = (await client.get(q)).json()

    groceries = [b for b in before["by_category"] if b["category_id"] == 1][0]
    assert (await client.delete("/api/categories/1")).status_code == 204

    after = (await client.get(q)).json()
    assert after["total_paise"] == before["total_paise"]
    assert after["count"] == before["count"]
    assert after["daily_average_paise"] == before["daily_average_paise"]

    unc = [b for b in after["by_category"] if b["category_id"] is None]
    assert len(unc) == 1
    assert unc[0]["category_name"] == "Uncategorised"
    assert unc[0]["total_paise"] >= groceries["total_paise"]
    assert sum(b["total_paise"] for b in after["by_category"]) == after["total_paise"]
    assert sum(b["percent"] for b in after["by_category"]) == 100
