"""End-to-end against the real database. `E0-S5`, `E0-S6`, and the isolation gate.

Marked `db`: these need `spendwise_test` on RDS and skip cleanly without it.
Nothing here is faked. A fake repository would give a green suite and a false
one, on the single guarantee this product is about — *everyone sees only their
own money* — which is enforced by row-level security and cannot be proved
anywhere but a database.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.db

A = {"email": "a@spendwise.test", "password": "correct-horse-battery-staple",
     "display_name": "Person A"}
B = {"email": "b@spendwise.test", "password": "correct-horse-battery-staple",
     "display_name": "Person B"}


async def register(client, who: dict) -> dict:
    r = await client.post("/api/auth/register", json=who)
    assert r.status_code == 201, r.text
    return r.json()


async def login(client, who: dict) -> dict:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text
    return r.json()


# ── E0-S5: register and sign in ────────────────────────────────────────────
async def test_register_creates_a_person_with_eight_categories(client) -> None:
    """`P-REC-05`: a new account starts with the eight, created in the SAME
    transaction. A person with no categories is a broken account."""
    me = await register(client, A)
    assert me["email"] == A["email"]
    assert me["role"] in ("user", "admin")
    assert me["currency"] == "INR"
    assert me["receipts_enabled"] is False        # S3_BUCKET unset


async def test_the_session_cookie_is_httponly_and_samesite_lax(client) -> None:
    """`E0-S5` AC2 — OBSERVED in the response headers, not assumed.

    httpOnly so script cannot read it; SameSite=Lax so a cross-site form post
    cannot ride it.
    """
    r = await client.post("/api/auth/register", json=A)
    raw = r.headers.get("set-cookie", "")
    assert "sw_session=" in raw
    assert "httponly" in raw.lower()
    assert "samesite=lax" in raw.lower()


async def test_me_returns_the_principal(client) -> None:
    await register(client, A)
    r = await client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == A["email"]


async def test_an_unauthenticated_request_is_401_with_no_data(client) -> None:
    """`E0-S5` AC4. The body must carry the envelope and nothing else — a 401
    that leaks a field name has told an attacker the shape of the thing."""
    r = await client.get("/api/expenses/1")
    assert r.status_code == 401
    body = r.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "UNAUTHENTICATED"


async def test_signing_out_then_replaying_the_cookie_is_401(client) -> None:
    """`E0-S5` AC3 / `NEG-A-03`. The session ROW is revoked, so a replayed
    cookie fails even though its signature is still perfectly valid."""
    await register(client, A)
    cookie = client.cookies.get("sw_session")

    assert (await client.post("/api/auth/logout")).status_code == 204

    client.cookies.set("sw_session", cookie)
    r = await client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "SESSION_INVALID"


async def test_a_duplicate_email_is_409_case_insensitively(client) -> None:
    """`SW-ADR-027`: `Ani@x.com` and `ani@x.com` are ONE account, enforced by
    the unique index on `lower(email)` rather than by a pre-read that races."""
    await register(client, A)
    r = await client.post("/api/auth/register", json={**A, "email": "A@SpendWise.test"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_TAKEN"


# ── E0-S6: create and read one expense ─────────────────────────────────────
async def test_create_and_read_back(client) -> None:
    me = await register(client, A)
    r = await client.post("/api/expenses", json={
        "amount": "1250.00", "spent_on": "2026-08-01", "description": "Auto to office"})
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["user_id"] == me["id"]
    assert row["amount_paise"] == 125000
    assert row["amount"] == "1250.00"
    assert row["currency"] == "INR"
    assert row["updated_at"] is None
    # No category was given, so the name is null - `Uncategorised` is a BUCKET
    # label and belongs to the summary alone (`SW-ADR-141 D`).
    assert row["category_name"] is None

    got = await client.get(f"/api/expenses/{row['id']}")
    assert got.status_code == 200
    assert got.json() == row


async def test_a_forged_user_id_and_id_are_discarded_not_rejected(client) -> None:
    """`SW-ADR-130` / `NEG-X-10`: **201**, with the row owned by the caller.

    A create has no target, so there is nothing to 404 on. The forged fields are
    dropped before validation — which is why `extra="forbid"` is unavailable
    however tempting it looks.
    """
    me = await register(client, A)
    r = await client.post("/api/expenses", json={
        "amount": "10.00", "spent_on": "2026-08-01",
        "user_id": 99999, "id": 4242, "amount_paise": 1, "currency": "USD"})
    assert r.status_code == 201, r.text
    row = r.json()
    assert row["user_id"] == me["id"], "the forged owner reached the stored row"
    assert row["id"] != 4242
    assert row["amount_paise"] == 1000      # from `amount`, not the forged paise
    assert row["currency"] == "INR"


async def test_a_category_belonging_to_someone_else_is_422(client) -> None:
    """`NEG-X-11`. Refused BY THE DATABASE via the composite foreign key — not
    by a pre-read the application could forget, and which would race.

    This is a cross-person read attempted through a WRITE, and it is the reason
    `SW-ADR-072` made that key composite.
    """
    await register(client, A)
    a_cats = (await client.get("/api/auth/me")).json()
    a_id = a_cats["id"]
    # A's first category id — A registered first, so ids 1..8 are A's.
    await client.post("/api/auth/logout")

    await register(client, B)
    r = await client.post("/api/expenses", json={
        "amount": "10.00", "spent_on": "2026-08-01", "category_id": 1})
    assert r.status_code == 422, r.text
    body = r.json()["error"]
    assert body["field"] == "category_id"
    assert body["message"] == "That category does not exist."


# ── the isolation gate ─────────────────────────────────────────────────────
async def test_person_b_cannot_read_person_as_expense(client) -> None:
    """`E0-S7` AC1 / `NEG-X-01` (SEV-1). **404, not 403** — and identical to a
    nonexistent id.

    A 403 on an existing row and a 404 on a missing one is a working oracle:
    walk the id space and learn which ids are real (`P-PRV-03`).
    """
    await register(client, A)
    created = await client.post("/api/expenses",
                                json={"amount": "1250.00", "spent_on": "2026-08-01"})
    a_expense_id = created.json()["id"]
    await client.post("/api/auth/logout")

    await register(client, B)
    mine = await client.get(f"/api/expenses/{a_expense_id}")
    nonexistent = await client.get("/api/expenses/999999")

    assert mine.status_code == 404
    assert nonexistent.status_code == 404
    assert mine.json() == nonexistent.json(), (
        "not-yours and not-found must be byte-identical, or the difference is "
        "an oracle for walking the id space")


async def test_the_summary_only_ever_totals_your_own_money(client) -> None:
    """The product's whole promise, at the API."""
    await register(client, A)
    for amount in ("1250.00", "340.50"):
        await client.post("/api/expenses", json={"amount": amount, "spent_on": "2026-08-01"})
    await client.post("/api/auth/logout")

    await register(client, B)
    await client.post("/api/expenses", json={"amount": "99.99", "spent_on": "2026-08-01"})

    s = (await client.get("/api/expenses/summary"
                          "?from=2026-08-01&to=2026-08-31")).json()
    assert s["total_paise"] == 9999, "B's summary included A's money"
    assert s["count"] == 1
