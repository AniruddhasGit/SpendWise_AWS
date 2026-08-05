"""M2 — expense list / update / delete.

`P-REC-02`, `P-REC-03`, `P-REC-04`. The list is where `SW-ADR-145`'s asymmetry
lives: `limit` is clamped and `offset` is refused, because the registry can
express one refusal and not the other.
"""
from __future__ import annotations

import pytest

from tests.seed import expenses_for, seed

pytestmark = [pytest.mark.db]

MONTH = "from=2026-08-01&to=2026-08-31"


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


# ── list ───────────────────────────────────────────────────────────────────
async def test_the_list_returns_your_four_newest_first(client, clean_db) -> None:
    """`P-REC-02`. Sorted `spent_on DESC` — the thing you just spent is the
    thing you are most likely looking for."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.get("/api/expenses")
    assert r.status_code == 200, r.text
    page = r.json()

    assert page["total"] == 4
    assert page["limit"] == 50
    assert page["offset"] == 0
    assert len(page["items"]) == 4

    dates = [i["spent_on"] for i in page["items"]]
    assert dates == sorted(dates, reverse=True)
    assert {i["amount_paise"] for i in page["items"]} == {9999, 34050, 125000, 210000}


async def test_total_is_a_row_count_not_a_money_total(client, clean_db) -> None:
    """`models.ExpensePage`'s note, asserted. 4, never 379049 — the two are
    both plausible integers on a field called `total`, which is why the contract
    wrote the note and why this test exists."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    page = (await client.get("/api/expenses")).json()
    assert page["total"] == 4
    assert page["total"] != 379049


async def test_each_row_carries_its_category_name(client, clean_db) -> None:
    """The sanctioned crossing (`SW-ADR-017`), through ONE lookup for the page —
    not one per row."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    items = (await client.get("/api/expenses")).json()["items"]

    named = {i["category_id"]: i["category_name"] for i in items}
    assert named[1] == "Groceries"
    assert named[3] == "Transport"
    assert named.get(None) is None, "a null category was given a synthetic name"


async def test_the_list_is_only_your_own(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])
    page = (await client.get("/api/expenses")).json()

    assert page["total"] == 2
    assert sum(i["amount_paise"] for i in page["items"]) == 125000
    assert all(i["user_id"] == made["B"]["id"] for i in page["items"])


async def test_pagination_pages_without_repeating_or_skipping(client, clean_db) -> None:
    """Two pages of two. The union must be the whole set — a sort with no
    tie-breaker shows a row twice here about one run in three."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    one = (await client.get("/api/expenses?limit=2&offset=0")).json()
    two = (await client.get("/api/expenses?limit=2&offset=2")).json()

    assert one["total"] == two["total"] == 4
    assert len(one["items"]) == len(two["items"]) == 2
    ids = [i["id"] for i in one["items"]] + [i["id"] for i in two["items"]]
    assert len(set(ids)) == 4, "a row appeared on both pages"


async def test_an_offset_past_the_end_is_an_empty_page_not_an_error(client,
                                                                    clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    page = (await client.get("/api/expenses?offset=999")).json()
    assert page["items"] == []
    assert page["total"] == 4, "total is the matching count, not the page length"


async def test_filtering_by_date_range_and_by_category(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.get("/api/expenses?category_id=1")
    assert r.status_code == 200
    assert all(i["category_id"] == 1 for i in r.json()["items"])

    day = expenses_for("A")[0]["spent_on"]
    r = await client.get(f"/api/expenses?from={day}&to={day}")
    assert all(i["spent_on"] == day for i in r.json()["items"])


# ── SW-ADR-145: the asymmetry ──────────────────────────────────────────────
async def test_an_over_large_limit_is_clamped_and_says_so(client, clean_db) -> None:
    """`SW-ADR-145 A`. 200, echoed in the body — never a 422, because the closed
    registry holds no rule capable of refusing it."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.get("/api/expenses?limit=500")
    assert r.status_code == 200, r.text
    assert r.json()["limit"] == 200, "the clamp was applied but not reported"


async def test_a_zero_or_negative_limit_clamps_up_to_one(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    for asked in (0, -3):
        page = (await client.get(f"/api/expenses?limit={asked}")).json()
        assert page["limit"] == 1
        assert len(page["items"]) == 1


async def test_a_negative_offset_is_422_with_the_offset_bounds_sentence(client,
                                                                        clean_db) -> None:
    """**`NEG-X-12`, SEV-1.** Naming `offset` is not enough — `field.type` also
    names `offset`, and would say "offset must be an integer, for example 0"
    about a value that IS an integer. The RULE has to be right (`SW-ADR-145 B`).
    """
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.get("/api/expenses?offset=-1")
    assert r.status_code == 422, r.text
    err = r.json()["error"]
    assert err["field"] == "offset"
    assert err["message"] == "offset must be zero or greater."


async def test_a_non_integer_offset_is_still_field_type(client, clean_db) -> None:
    """`SW-ADR-145 C`. The clamp and the bounds rule apply to integers; they
    never coerce something that is not one."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])

    r = await client.get("/api/expenses?offset=abc")
    assert r.status_code == 422
    assert r.json()["error"]["field"] == "offset"
    assert r.json()["error"]["message"] == "offset must be an integer, for example 0."

    r = await client.get("/api/expenses?limit=abc")
    assert r.json()["error"]["message"] == "limit must be an integer, for example 50."


# ── update ─────────────────────────────────────────────────────────────────
async def test_patching_the_amount_changes_the_row_and_the_summary(client,
                                                                   clean_db) -> None:
    """`P-REC-03`. The summary is recomputed from rows, so an edit moves it —
    the same property `test_gate_75810` proves by editing the database directly,
    proved here through the endpoint a person actually uses."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    before = (await client.get(f"/api/expenses/summary?{MONTH}")).json()["total_paise"]

    target = made["A"]["expenses"][0]
    r = await client.patch(f"/api/expenses/{target['id']}", json={"amount": "1000.00"})
    assert r.status_code == 200, r.text
    assert r.json()["amount_paise"] == 100000
    assert r.json()["amount"] == "1000.00"

    after = (await client.get(f"/api/expenses/summary?{MONTH}")).json()["total_paise"]
    assert after == before - target["amount_paise"] + 100000


async def test_updated_at_is_set_on_edit_and_null_before_it(client, clean_db) -> None:
    """`CV-09`. The SERVICE sets it, never a trigger — a trigger would fire on
    writes that are not edits and make "never edited" unrepresentable."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    target = made["A"]["expenses"][0]
    assert target["updated_at"] is None, "a fresh row already claimed to be edited"

    r = await client.patch(f"/api/expenses/{target['id']}", json={"description": "Edited"})
    assert r.status_code == 200, r.text
    assert r.json()["updated_at"] is not None


async def test_patching_the_category_relabels_and_renames(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    target = made["A"]["expenses"][0]

    r = await client.patch(f"/api/expenses/{target['id']}", json={"category_id": 3})
    assert r.status_code == 200, r.text
    assert r.json()["category_id"] == 3
    assert r.json()["category_name"] == "Transport"


async def test_patching_onto_someone_elses_category_is_422_naming_category_id(
        client, clean_db) -> None:
    """`NEG-X-11`, on the update path. Refused by the composite FK — the same
    guard as create, not a second hand-written check that could drift."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])
    target = made["B"]["expenses"][0]

    r = await client.patch(f"/api/expenses/{target['id']}", json={"category_id": 1})
    assert r.status_code == 422, r.text
    assert r.json()["error"]["field"] == "category_id"
    assert r.json()["error"]["message"] == "That category does not exist."


async def test_an_empty_patch_is_422_naming_body(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch(f"/api/expenses/{made['A']['expenses'][0]['id']}", json={})
    assert r.status_code == 422, r.text
    assert r.json()["error"]["field"] == "body"


@pytest.mark.parametrize(("body", "field", "message"), [
    ({"amount": "12.345"}, "amount", "Amount must have at most two decimal places."),
    ({"amount": "0.00"}, "amount",
     "Amount must be greater than zero and at most 10000000000.00."),
    ({"amount": "abc"}, "amount", 'Amount must be a decimal string, for example "1250.00".'),
    ({"spent_on": "1990-01-01"}, "spent_on",
     "Date must be within the last 10 years and no more than 1 year ahead."),
    ({"description": "x" * 501}, "description",
     "Description must be at most 500 characters."),
])
async def test_patch_applies_the_same_rules_as_create(client, clean_db, body,
                                                      field, message) -> None:
    """The validation is shared, so it cannot drift between the two paths — an
    amount refused on create and accepted on update is the classic hole."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    r = await client.patch(f"/api/expenses/{made['A']['expenses'][0]['id']}", json=body)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["field"] == field
    assert r.json()["error"]["message"] == message


async def test_a_rejected_patch_changes_nothing(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    target = made["A"]["expenses"][0]

    await client.patch(f"/api/expenses/{target['id']}",
                       json={"amount": "1000.00", "spent_on": "1990-01-01"})
    still = (await client.get(f"/api/expenses/{target['id']}")).json()
    assert still["amount_paise"] == target["amount_paise"], "a rejected patch half-applied"
    assert still["updated_at"] is None


async def test_patching_someone_elses_expense_is_404(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    a_expense = made["A"]["expenses"][0]["id"]
    await _sign_in(client, made["B"])

    r = await client.patch(f"/api/expenses/{a_expense}", json={"amount": "1.00"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"

    # And it really was not applied.
    await client.post("/api/auth/logout")
    await _sign_in(client, made["A"])
    assert (await client.get(f"/api/expenses/{a_expense}")).json()["amount_paise"] \
        == made["A"]["expenses"][0]["amount_paise"]


async def test_a_forged_user_id_in_a_patch_is_discarded_not_rejected(client,
                                                                     clean_db) -> None:
    """`SW-ADR-130`, on the update path. `extra="ignore"`, so the key never
    reaches validation — 200, and the row still belongs to the caller."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    target = made["A"]["expenses"][0]

    r = await client.patch(f"/api/expenses/{target['id']}",
                           json={"description": "ok", "user_id": made["B"]["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["user_id"] == made["A"]["id"]


# ── delete ─────────────────────────────────────────────────────────────────
async def test_delete_removes_the_row_and_the_money(client, clean_db) -> None:
    """`P-REC-04`. Unlike a category, deleting an EXPENSE really deletes it —
    the expense IS the record, so there is nothing left to preserve."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    target = made["A"]["expenses"][0]
    before = (await client.get(f"/api/expenses/summary?{MONTH}")).json()

    r = await client.delete(f"/api/expenses/{target['id']}")
    assert r.status_code == 204
    assert r.content == b""

    assert (await client.get(f"/api/expenses/{target['id']}")).status_code == 404
    after = (await client.get(f"/api/expenses/summary?{MONTH}")).json()
    assert after["total_paise"] == before["total_paise"] - target["amount_paise"]
    assert after["count"] == before["count"] - 1
    assert (await client.get("/api/expenses")).json()["total"] == 3


async def test_deleting_twice_is_404_the_second_time(client, clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    target = made["A"]["expenses"][0]["id"]
    assert (await client.delete(f"/api/expenses/{target}")).status_code == 204
    assert (await client.delete(f"/api/expenses/{target}")).status_code == 404


async def test_deleting_someone_elses_expense_is_404_and_leaves_it_alone(client,
                                                                         clean_db) -> None:
    made = await seed(client, guard_database=clean_db)
    a_expense = made["A"]["expenses"][0]["id"]
    await _sign_in(client, made["B"])
    assert (await client.delete(f"/api/expenses/{a_expense}")).status_code == 404

    await client.post("/api/auth/logout")
    await _sign_in(client, made["A"])
    assert (await client.get(f"/api/expenses/{a_expense}")).status_code == 200


async def test_deleting_a_category_does_not_delete_expenses_but_deleting_an_expense_does(
        client, clean_db) -> None:
    """The two deletes side by side, because the asymmetry is the design and a
    reader who has only seen one of them will assume the other matches."""
    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["A"])
    before = (await client.get("/api/expenses")).json()["total"]

    assert (await client.delete("/api/categories/1")).status_code == 204
    assert (await client.get("/api/expenses")).json()["total"] == before

    assert (await client.delete(
        f"/api/expenses/{made['A']['expenses'][0]['id']}")).status_code == 204
    assert (await client.get("/api/expenses")).json()["total"] == before - 1
