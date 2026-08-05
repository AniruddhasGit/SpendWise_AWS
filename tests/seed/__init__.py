"""The day-one seed.

**Lives under the test tree, never in the built image** (`SW-ADR-086`) — a
seeder reachable in a deployed environment is an unauthenticated
account-creation backdoor on a host that runs without TLS.

It drives the **real registration and expense endpoints**, not direct SQL.
Seeding by `INSERT` would skip the eight-category creation and the
password-hashing path, so the gate would prove less than it claims — and would
not have caught the row-level-security ordering bug in registration that it did.

Every value comes from `docs/03 PRD/api/contract.json`. Nothing here is typed.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

CONTRACT = (Path(__file__).resolve().parents[2]
            / "docs" / "03 PRD" / "api" / "contract.json")

TEST_DB_NAME = "spendwise_test"


@lru_cache(maxsize=1)
def fixture() -> dict:
    return json.loads(CONTRACT.read_text("utf-8"))["seed_fixture"]


def people() -> list[dict]:
    """Exactly two, in registration order.

    `SRC-001` ERRATUM E-6 and `CONSTITUTION` Art IX.4 both say **two users
    seeded**. The order matters: A registers first, so A's eight categories take
    identity values 1–8, which is what makes `expected_summary.json`'s
    `category_id` 1, 3 and 5 mean Groceries, Transport and Health.
    """
    return sorted(fixture()["people"], key=lambda p: p["registration_order"])


def expenses_for(person: str) -> list[dict]:
    return fixture()["expenses_by_person"][person]


# The fixture's category ids are ABSOLUTE, not per-person offsets: A's are 1-8
# and B's are 9-16, and the contract states B's as 9 rather than as "B's first".
# An earlier version of this file treated them as offsets and turned B's 9 into
# 17, which the composite foreign key correctly refused.
#
# That makes the seed depend on identity values starting at 1, which is exactly
# why `CV-24` mandates TRUNCATE ... RESTART IDENTITY CASCADE. Without it the
# second test case gets 17-24 and this fails loudly here rather than producing
# silently wrong `by_category` assertions later.


async def seed(client, *, guard_database: str | None = None) -> dict:
    """Create both people and their expenses through the API.

    Returns `{"A": {...}, "B": {...}}` with each person's id, their category
    ids, and their expense ids.
    """
    if guard_database is not None and TEST_DB_NAME not in guard_database:
        # SW-ADR-086. The seeder refuses to run anywhere but the test database —
        # it creates accounts with known passwords, and that is only ever safe
        # against a database that is dropped and rebuilt.
        raise RuntimeError(
            f"refusing to seed: the target is not {TEST_DB_NAME}. The seed creates "
            f"accounts with known passwords and must never touch a real database.")

    out: dict[str, dict] = {}
    for person in people():
        r = await client.post("/api/auth/register", json={
            "email": person["email"], "password": person["password"],
            "display_name": person["display_name"]})
        if r.status_code != 201:
            raise RuntimeError(f"register {person['person']} failed: {r.status_code} {r.text}")
        me = r.json()

        made = []
        for e in expenses_for(person["person"]):
            body = {"amount": _rupees(e["amount_paise"]), "spent_on": e["spent_on"]}
            if e["category_id"] is not None:
                body["category_id"] = e["category_id"]
            if e.get("description"):
                body["description"] = e["description"]
            rr = await client.post("/api/expenses", json=body)
            if rr.status_code != 201:
                raise RuntimeError(
                    f"create expense for {person['person']} failed: {rr.status_code} {rr.text}")
            made.append(rr.json())

        out[person["person"]] = {
            "id": me["id"], "email": person["email"], "password": person["password"],
            "expenses": made,
        }
        await client.post("/api/auth/logout")

    return out


def _rupees(paise: int) -> str:
    return f"{paise // 100}.{paise % 100:02d}"
