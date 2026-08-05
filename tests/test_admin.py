"""M4 — the admin module. Six stories.

The one that carries the product is **E4-S2**: no admin response model may
declare a field capable of holding an amount or a description. `SRC-001 §4.2`,
the client's own permission matrix:

    | See anyone else's expense amounts | user: no | admin: **no** |

The bold **no** is theirs. That is asserted here by introspecting the Pydantic
models and by querying `pg_policies` — not by reading the handlers, because a
handler is one careless join away from returning a row it should not.
"""
from __future__ import annotations

import pytest

from tests.seed import seed

pytestmark = [pytest.mark.db]

PASSWORD = "correct-horse-battery-staple"


def flatten(routes):
    """Every real route, descending through included routers.

    This FastAPI keeps an included router as an **`_IncludedRouter` wrapper**
    in `app.routes` — it has no `.path` and no `.routes`, only
    `.original_router`. So the obvious
    `[r for r in app.routes if r.path.startswith("/api/admin")]` finds
    **nothing**, and a test written that way passes by having zero routes to
    check. That is exactly the shape of green this file exists to prevent,
    which is why it descends and why the caller asserts the list is non-empty.
    """
    out = []
    for r in routes:
        inner = getattr(r, "original_router", None) or (
            r if hasattr(r, "routes") else None)
        if inner is not None and inner is not r:
            out.extend(flatten(inner.routes))
        elif inner is not None:
            out.extend(flatten(inner.routes))
        else:
            out.append(r)
    return out


async def _sign_in(client, who: dict) -> None:
    r = await client.post("/api/auth/login",
                          json={"email": who["email"], "password": who["password"]})
    assert r.status_code == 200, r.text


async def _make_admin(client, clean_db, test_urls):
    """Promote person A by hand, as the owner, then sign them in.

    Direct SQL rather than an endpoint: promoting requires an admin, and this
    fixture exists to create the first one. `SRC-001 §4.4`'s bootstrap does the
    same job in production; doing it that way here would couple every admin
    test to `BOOTSTRAP_ADMIN_EMAIL`.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    made = await seed(client, guard_database=clean_db)
    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.begin() as c:
        await c.execute(text("UPDATE users SET role = 'admin' WHERE id = :i"),
                        {"i": made["A"]["id"]})
    await e.dispose()
    await _sign_in(client, made["A"])
    return made


# ── E4-S1: require_admin, applied once ─────────────────────────────────────
def test_every_admin_route_declares_the_guard_on_the_router() -> None:
    """AC1, asserted by **walking the route table**, not by listing routes.

    A hand-written list is one forgotten line away from an unprotected
    endpoint, and the forgetting is silent. This finds the routes the way
    FastAPI does.
    """
    from app.core.deps import require_admin
    from app.main import app

    admin_routes = [r for r in flatten(app.routes)
                    if getattr(r, "path", "").startswith("/api/admin")]
    assert admin_routes, "no admin routes were registered at all"

    for route in admin_routes:
        names = [d.call.__name__ for d in route.dependant.dependencies
                 if getattr(d, "call", None)]
        flat = " ".join(names)
        assert require_admin.__name__ in flat, (
            f"{route.path} does not carry require_admin")


def test_no_handler_contains_its_own_role_check() -> None:
    """AC2. The check is declared ONCE, on the router.

    `SRC-001 §4.3`, the client's words: *"One place, not a check copy-pasted
    into every handler, because I will forget one."* A grep is the right shape
    of test for that, because the failure it prevents is a handler that has one
    and a handler that does not.
    """
    from pathlib import Path

    source = Path("app/modules/admin/router.py").read_text(encoding="utf-8")
    body = "\n".join(l for l in source.split("\n")
                     if not l.strip().startswith(("#", "*", '"""')))
    assert 'role != "admin"' not in body
    assert "role == 'admin'" not in body
    assert body.count("Depends(require_admin)") == 1


async def test_a_plain_user_is_refused_from_every_admin_route(client, clean_db) -> None:
    """AC1. Every route, driven — walked from the app, so a route added later
    is covered without this test being edited."""
    from app.main import app

    made = await seed(client, guard_database=clean_db)
    await _sign_in(client, made["B"])

    routes = [r for r in flatten(app.routes)
              if getattr(r, "path", "").startswith("/api/admin")]
    assert len(routes) >= 8, routes

    # The methods each route ACTUALLY declares. Trying GET on a POST-only route
    # returns 404 — the SPA catch-all answers it — which is neither a pass nor
    # a failure of this criterion, and treating it as either would be wrong.
    checked = 0
    for route in routes:
        url = route.path.replace("{user_id}", str(made["A"]["id"]))
        for method in sorted(m for m in route.methods if m in ("GET", "POST")):
            r = await client.request(
                method, url, **({"json": {}} if method == "POST" else {}))
            assert r.status_code == 403, f"{method} {url} -> {r.status_code}"
            assert r.json()["error"]["code"] == "FORBIDDEN"
            checked += 1
    assert checked >= 8, f"only {checked} admin endpoints were actually driven"


async def test_an_unauthenticated_caller_is_401_not_403(client, clean_db) -> None:
    """The order matters: 403 would confirm the route exists to someone who has
    not identified themselves at all."""
    r = await client.get("/api/admin/users")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"


# ── E4-S2: the models cannot carry money ───────────────────────────────────
MONEY_WORDS = ("amount", "paise", "total", "sum", "money", "price", "cost",
               "value", "description", "note", "spent_on", "currency")

# `CR-001` exempts exactly TWO models, and this is the list. A tuple of NAMES
# rather than a looser rule — "anything ending in Spending", "anything the admin
# service builds" — because a rule with a shape can be satisfied by a model
# nobody meant to exempt, and a list cannot. Adding a third is an edit to this
# line, which is one line in a diff and impossible to miss.
SPENDING_MODELS = ("AdminUserSpending", "SpendingDay")

# Named, because an introspection test that reaches nothing PASSES. A renamed
# module, a moved class or a `schemas.py` split in two would find zero models to
# fail on and report green on the guarantee this file exists for.
MUST_STILL_BE_CLEAN = ("AdminUser", "AdminSession", "AuditRow", "AdminOverview")


def admin_models() -> dict:
    """Every Pydantic model DECLARED in `admin.schemas`, keyed by class name.

    `cls.__module__` check included: `inspect.getmembers` returns everything
    *imported* into the module too, and without it this walks `BaseModel`'s
    imports and half of Pydantic.
    """
    import inspect

    from pydantic import BaseModel

    from app.modules.admin import schemas

    return {name: cls for name, cls in inspect.getmembers(schemas, inspect.isclass)
            if issubclass(cls, BaseModel) and cls is not BaseModel
            and cls.__module__ == schemas.__name__}


def test_no_admin_response_model_can_hold_an_amount_or_a_description() -> None:
    """**AC1, by introspection — and `CR-001` moved ONE of the two lines.**

    `SRC-001 §4.2` refused an administrator every amount; `CR-001` reversed that
    half by name, so the money rule is no longer universal. The exemption is
    therefore written down HERE, by name, instead of the rule being loosened
    everywhere:

        `AdminUserSpending`, and `SpendingDay` — which exists only as its
        `by_day` rows — are the ONLY models in `admin.schemas` that may declare
        a field capable of holding money. Nothing else may, and a second model
        gaining one fails this test rather than passing it quietly.

    The exemption is inert until those classes exist; `tests/test_admin_spending.py`
    is what proves they do, and proves the endpoint behind them returns the
    person's real total. If a model appears under some OTHER name carrying
    `total_paise`, this test fails — correctly, because `CR-001 §2` names the
    response model and a divergence there is a contract break, not a style
    choice.

    **The other half of the client's sentence did not move**, and it is the half
    the whole design now rests on:

        *"the expenses that are happening not the categories spent on"*

    That is asserted SEPARATELY below, over **every** model including the two
    exempt ones, with no exemption at all: `CR-001` granted the amount and
    refused the label, so a field matching `categor` or `description` is
    forbidden everywhere in this module. It is mechanical on purpose — a
    reviewer greps this module for `categor` and finds nothing, and so does
    this.

    One thing tightened while rewriting: the bare name `total` used to sit on
    the allowlist as a row count and would have sailed through **on any model
    at all**, including `AdminUser`. It is now allowed only on a `*Page`, which
    is the only place a row count lives.

    Introspection rather than review, because this is the guarantee the whole
    product is about and a reviewer reads a diff once.
    """
    models = admin_models()
    assert len(models) >= 8, f"only {len(models)} models introspected — did the module move?"
    for required in MUST_STILL_BE_CLEAN:
        assert required in models, (
            f"{required} was not found in admin.schemas — this test cannot "
            f"assert anything about a model it cannot reach")

    # ── 1. money: forbidden on every model but the two CR-001 named ────────
    for name, cls in models.items():
        if name in SPENDING_MODELS:
            continue
        for field in cls.model_fields:
            low = field.lower()
            if low.endswith("_count") or low.startswith("accounts_") or low in (
                    "count", "limit", "offset", "admins", "sessions_live",
                    "expenses_recorded", "audit_last_7_days"):
                continue
            # A row count, and only where rows are counted.
            if low == "total" and name.endswith("Page"):
                continue
            for word in MONEY_WORDS:
                assert word not in low, (
                    f"{name}.{field} could carry money or a description "
                    f"(matched {word!r}). CR-001 exempts {SPENDING_MODELS} and "
                    f"nothing else — SRC-001 §4.2 still holds for {name}")

    # ── 2. the label: forbidden EVERYWHERE, exemptions included ────────────
    # The line CR-001 draws, asserted mechanically. `AdminUserSpending` carries
    # a total precisely so that it can carry nothing else, and a `by_category`
    # arriving on it later would be the change request read backwards.
    for name, cls in models.items():
        for field in cls.model_fields:
            low = field.lower()
            assert "categor" not in low, (
                f"{name}.{field} is a CATEGORY field. CR-001 granted the amount "
                f"and refused the label: 'the expenses that are happening not "
                f"the categories spent on'")
            assert "description" not in low, (
                f"{name}.{field} could hold a description. CR-001 grants an "
                f"administrator how much, never what for")


def test_the_session_model_declares_no_ip_and_no_user_agent() -> None:
    """AC2. `SW-ADR-106`, `NEG-R-10`. "Who is signed in" is an operational
    question; answering it does not require a location history."""
    from app.modules.admin.schemas import AdminSession

    fields = set(AdminSession.model_fields)
    assert "ip" not in fields
    assert "user_agent" not in fields


async def test_no_policy_on_expenses_or_categories_consults_is_admin(
        client, clean_db, test_urls) -> None:
    """AC3, asked of **PostgreSQL**, not of the code.

    A policy that lets an admin count rows lets them SELECT every column of
    those rows. `SW-ADR-129` replaced exactly such a policy with a
    `SECURITY DEFINER` function, and this is the assertion that keeps it gone.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.connect() as c:
        rows = (await c.execute(text(
            "SELECT tablename, policyname, qual, with_check FROM pg_policies "
            "WHERE tablename IN ('expenses','categories')"))).all()
    await e.dispose()

    assert rows, "no policies at all on expenses/categories"
    for table, name, qual, check in rows:
        blob = f"{qual or ''} {check or ''}"
        assert "is_admin" not in blob, (
            f"policy {name} on {table} consults app.is_admin — an admin who can "
            f"count rows through a policy can read every column of them")


async def test_admin_expense_stats_returns_exactly_two_columns(client, clean_db,
                                                               test_urls) -> None:
    """AC4. The bypass is bounded by the FUNCTION SIGNATURE, not by the
    discipline of whoever writes the next query against it."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    _, owner_url = test_urls
    e = create_async_engine(owner_url, poolclass=None)
    async with e.connect() as c:
        sig = (await c.execute(text(
            "SELECT pg_get_function_result(oid) FROM pg_proc "
            "WHERE proname = 'admin_expense_stats'"))).scalar_one()
    await e.dispose()

    assert sig.count(",") == 1, f"the function returns more than two columns: {sig}"
    assert "expense_count" in sig and "last_activity" in sig
    for word in ("amount", "paise", "description"):
        assert word not in sig.lower()


async def test_the_user_list_carries_counts_and_no_amounts(client, clean_db,
                                                           test_urls) -> None:
    """Driven, not introspected: the payload a real admin receives, checked for
    the four amounts person A actually has."""
    made = await _make_admin(client, clean_db, test_urls)

    r = await client.get("/api/admin/users")
    assert r.status_code == 200, r.text
    body = r.text

    for amount in ("210000", "125000", "34050", "9999", "2100.00", "1250.00"):
        assert amount not in body, f"the admin user list leaked {amount}"

    rows = {u["id"]: u for u in r.json()["items"]}
    assert rows[made["A"]["id"]]["expense_count"] == 4
    assert rows[made["B"]["id"]]["expense_count"] == 2
    assert rows[made["A"]["id"]]["last_activity"] == "2026-08-05"


# ── E4-S6: listing and reading ─────────────────────────────────────────────
async def test_the_user_list_paginates_and_searches(client, clean_db, test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)

    page = (await client.get("/api/admin/users?limit=1&offset=0")).json()
    assert page["total"] == 2
    assert len(page["items"]) == 1
    assert page["limit"] == 1

    by_email = (await client.get("/api/admin/users?q=b@spendwise")).json()
    assert [u["id"] for u in by_email["items"]] == [made["B"]["id"]]

    by_name = (await client.get("/api/admin/users?q=person a")).json()
    assert [u["id"] for u in by_name["items"]] == [made["A"]["id"]]

    admins = (await client.get("/api/admin/users?role=admin")).json()
    assert [u["id"] for u in admins["items"]] == [made["A"]["id"]]


async def test_an_over_large_limit_is_clamped_and_echoed(client, clean_db,
                                                         test_urls) -> None:
    """`SW-ADR-145 A`, same reasoning on this router: the closed registry holds
    no rule that can refuse an over-large page size."""
    await _make_admin(client, clean_db, test_urls)
    page = (await client.get("/api/admin/users?limit=9999")).json()
    assert page["limit"] == 200


async def test_the_session_list_shows_live_sessions_without_ip(client, clean_db,
                                                               test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    page = (await client.get("/api/admin/sessions")).json()

    assert page["total"] >= 1
    for s in page["items"]:
        assert "ip" not in s
        assert "user_agent" not in s
        assert s["revoked_at"] is None


async def test_the_audit_log_renders_sentences_not_raw_json(client, clean_db,
                                                            test_urls) -> None:
    """AC3. A client assembling these would need to know all nine action types
    and would print `[object Object]` for the tenth — and the tenth is exactly
    the row an auditor most needs to read."""
    made = await _make_admin(client, clean_db, test_urls)
    await client.post(f"/api/admin/users/{made['B']['id']}/revoke-sessions")

    page = (await client.get("/api/admin/audit")).json()
    assert page["total"] >= 1
    assert [r["id"] for r in page["items"]] == sorted(
        (r["id"] for r in page["items"]), reverse=True), "not newest-first"

    revoked = [r for r in page["items"] if r["action"] == "sessions_revoked"]
    assert revoked, page["items"]
    assert "signed user #" in revoked[0]["sentence"]
    assert "{" not in revoked[0]["sentence"], "raw JSON reached the sentence"


# ── E4-S5: the audit record ────────────────────────────────────────────────
async def test_reading_the_user_list_writes_exactly_one_read_audit_row(
        client, clean_db, test_urls) -> None:
    """Looking at who exists is itself an exercise of privilege."""
    await _make_admin(client, clean_db, test_urls)

    before = (await client.get("/api/admin/audit")).json()["total"]
    await client.get("/api/admin/users")
    after = (await client.get("/api/admin/audit")).json()["total"]

    # TWO, not one. Each audit read reports the total as it stood BEFORE its
    # own row is written — deliberately, so a reader never finds the record of
    # their own read inside the page that produced it. So the delta is the
    # users read (1) plus the first audit read's own row (1).
    assert after - before == 2, f"{before} -> {after}"


async def test_every_mutation_writes_exactly_one_row(client, clean_db,
                                                     test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]

    for call in (
        lambda: client.post(f"/api/admin/users/{b}/revoke-sessions"),
        lambda: client.post(f"/api/admin/users/{b}/active", json={"is_active": False}),
        lambda: client.post(f"/api/admin/users/{b}/active", json={"is_active": True}),
        lambda: client.post(f"/api/admin/users/{b}/role", json={"role": "admin"}),
        lambda: client.post(f"/api/admin/users/{b}/role", json={"role": "user"}),
    ):
        before = (await client.get("/api/admin/audit?limit=1")).json()["total"]
        r = await call()
        assert r.status_code == 200, r.text
        after = (await client.get("/api/admin/audit?limit=1")).json()["total"]
        # 1 for the mutation + 1 for the first audit read's own row.
        assert after - before == 2, f"{r.request.url} wrote {after - before - 1} rows"


async def test_an_action_outside_the_nine_is_refused_before_the_write(
        client, clean_db, test_urls) -> None:
    """AC4. The CHECK constraint would catch it too — as an IntegrityError that
    aborts the transaction, so a typo would take the change with it and surface
    as a 500."""
    from app.modules.admin.repository import AdminRepository

    await _make_admin(client, clean_db, test_urls)
    repo = AdminRepository(db=None)                       # never touched
    with pytest.raises(ValueError, match="not one of the nine"):
        await repo.write_audit(admin_id=1, action="deleted_everything")


async def test_a_failed_audit_write_rolls_back_the_change(client, clean_db,
                                                          test_urls, monkeypatch) -> None:
    """**AC2, the one that proves `SRC-001 §10.8`.**

    > If the audit write fails, the change doesn't happen either.

    A failure is planted in the audit write and the change is then checked to
    have not happened. This is why no method in `AdminService` wraps the audit
    row in a savepoint: a savepoint would let the change survive.
    """
    from app.modules.admin.repository import AdminRepository

    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]

    real = AdminRepository.write_audit

    async def explode(self, **kw):
        if kw.get("action") == "user_deactivated":
            raise RuntimeError("planted: the audit write failed")
        return await real(self, **kw)

    monkeypatch.setattr(AdminRepository, "write_audit", explode)
    # The exception propagates out of ASGITransport rather than becoming a 500:
    # httpx re-raises application exceptions by default, which is the right
    # default for a test client and means the assertion is about the DATABASE,
    # not about the status code.
    with pytest.raises(RuntimeError, match="planted"):
        await client.post(f"/api/admin/users/{b}/active", json={"is_active": False})
    monkeypatch.undo()

    still = (await client.get("/api/admin/users")).json()
    target = [u for u in still["items"] if u["id"] == b][0]
    assert target["is_active"] is True, (
        "the deactivation survived a failed audit write — SRC-001 §10.8 says "
        "they commit together or neither does")


# ── E4-S3: reset, revoke, deactivate ───────────────────────────────────────
async def test_revoking_sessions_signs_the_person_out(client, clean_db,
                                                      test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    r = await client.post(f"/api/admin/users/{made['B']['id']}/revoke-sessions")
    assert r.status_code == 200
    assert r.json()["revoked"] >= 0

    # B's old cookie is gone from this client, so prove it by counting.
    live = (await client.get(f"/api/admin/sessions?user_id={made['B']['id']}")).json()
    assert live["total"] == 0


async def test_deactivating_refuses_sign_in_with_the_same_generic_401(
        client, clean_db, test_urls) -> None:
    """AC2. The SAME refusal as a wrong password — a distinct one would tell an
    attacker that the address exists and has been disabled."""
    made = await _make_admin(client, clean_db, test_urls)
    await client.post(f"/api/admin/users/{made['B']['id']}/active",
                      json={"is_active": False})
    await client.post("/api/auth/logout")

    deactivated = await client.post(
        "/api/auth/login", json={"email": made["B"]["email"],
                                 "password": made["B"]["password"]})
    wrong = await client.post(
        "/api/auth/login", json={"email": made["B"]["email"], "password": "x" * 14})

    assert deactivated.status_code == 401
    assert deactivated.json() == wrong.json(), (
        "a deactivated account and a wrong password gave different answers")


async def test_an_in_flight_session_is_refused_with_account_deactivated(
        client, clean_db, test_urls) -> None:
    """AC3. The role and `is_active` are re-read every request, so the refusal
    lands on the next call rather than in thirty days."""
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]

    # B holds a live session on their own client.
    import httpx
    from app.main import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://testserver") as b_client:
        await _sign_in(b_client, made["B"])
        assert (await b_client.get("/api/auth/me")).status_code == 200

        await client.post(f"/api/admin/users/{b}/active", json={"is_active": False})

        r = await b_client.get("/api/auth/me")
        assert r.status_code == 401
        assert r.json()["error"]["code"] in ("ACCOUNT_DEACTIVATED", "SESSION_INVALID")


async def test_reactivating_does_not_restore_any_revoked_session(
        client, clean_db, test_urls) -> None:
    """AC4. Revocation is a fact about a row, not a computed view of
    `is_active` — otherwise deactivating and reactivating would hand an
    attacker their session back."""
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]

    await client.post(f"/api/admin/users/{b}/active", json={"is_active": False})
    await client.post(f"/api/admin/users/{b}/active", json={"is_active": True})

    live = (await client.get(f"/api/admin/sessions?user_id={b}")).json()
    assert live["total"] == 0


async def test_issuing_a_reset_revokes_every_session_in_the_same_transaction(
        client, clean_db, test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]

    r = await client.post(f"/api/admin/users/{b}/reset")
    assert r.status_code == 200, r.text
    assert r.json()["token"]
    assert (await client.get(f"/api/admin/sessions?user_id={b}")).json()["total"] == 0


async def test_the_reset_token_can_be_redeemed_once(client, clean_db,
                                                    test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    token = (await client.post(
        f"/api/admin/users/{made['B']['id']}/reset")).json()["token"]
    await client.post("/api/auth/logout")

    new = "a-brand-new-passphrase-entirely"
    r = await client.post("/api/auth/reset/complete",
                          json={"token": token, "new_password": new})
    assert r.status_code == 204, r.text

    assert (await client.post("/api/auth/login",
                              json={"email": made["B"]["email"],
                                    "password": new})).status_code == 200
    await client.post("/api/auth/logout")

    # Used once, and only once.
    again = await client.post("/api/auth/reset/complete",
                              json={"token": token, "new_password": "another-one-here"})
    assert again.status_code == 401


async def test_an_unknown_expired_and_used_token_all_give_one_message(
        client, clean_db, test_urls) -> None:
    """`P-ACC-07`. Three states, one sentence — telling an attacker which one
    they hit turns a guessed token into an oracle."""
    made = await _make_admin(client, clean_db, test_urls)
    token = (await client.post(
        f"/api/admin/users/{made['B']['id']}/reset")).json()["token"]
    await client.post("/api/auth/logout")

    unknown = await client.post("/api/auth/reset/complete",
                                json={"token": "nope", "new_password": "x" * 14})
    await client.post("/api/auth/reset/complete",
                      json={"token": token, "new_password": "first-use-of-this-one"})
    used = await client.post("/api/auth/reset/complete",
                             json={"token": token, "new_password": "x" * 14})

    assert unknown.status_code == used.status_code == 401
    assert unknown.json() == used.json()


# ── E4-S4: roles and the last-administrator guard ──────────────────────────
async def test_promoting_applies_on_the_very_next_request(client, clean_db,
                                                          test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]
    assert (await client.post(f"/api/admin/users/{b}/role",
                              json={"role": "admin"})).json()["revoked"] == 0

    import httpx
    from app.main import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://testserver") as b_client:
        await _sign_in(b_client, made["B"])
        assert (await b_client.get("/api/admin/users")).status_code == 200


async def test_demoting_revokes_every_session(client, clean_db, test_urls) -> None:
    """Promotion does not revoke; demotion does. Signing someone out to give
    them MORE access is gratuitous; signing them out on the way down makes the
    change immediate rather than merely eventual."""
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]
    await client.post(f"/api/admin/users/{b}/role", json={"role": "admin"})

    import httpx
    from app.main import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://testserver") as b_client:
        await _sign_in(b_client, made["B"])
        assert (await b_client.get("/api/auth/me")).status_code == 200

        await client.post(f"/api/admin/users/{b}/role", json={"role": "user"})
        assert (await b_client.get("/api/auth/me")).status_code == 401


async def test_demoting_the_last_admin_is_409(client, clean_db, test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    r = await client.post(f"/api/admin/users/{made['A']['id']}/role",
                          json={"role": "user"})
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "CONFLICT"
    assert (await client.get("/api/auth/me")).json()["role"] == "admin"


async def test_deactivating_the_last_admin_is_409(client, clean_db, test_urls) -> None:
    """The guard watches DEACTIVATION too. Deactivating the last admin leaves a
    system nobody can administer, and it does it without touching the role
    column — so a guard that only watched roles would miss it entirely."""
    made = await _make_admin(client, clean_db, test_urls)
    r = await client.post(f"/api/admin/users/{made['A']['id']}/active",
                          json={"is_active": False})
    assert r.status_code == 409, r.text


async def test_a_deactivated_admin_does_not_count_toward_the_guard(
        client, clean_db, test_urls) -> None:
    """**Active** admins, not merely `role='admin'`. A deactivated admin cannot
    sign in, so counting them would let the last usable administrator be
    demoted while the guard reported two."""
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]

    await client.post(f"/api/admin/users/{b}/role", json={"role": "admin"})
    await client.post(f"/api/admin/users/{b}/active", json={"is_active": False})

    # A is now the only ACTIVE admin, even though two rows say `admin`.
    r = await client.post(f"/api/admin/users/{made['A']['id']}/role",
                          json={"role": "user"})
    assert r.status_code == 409, "a deactivated admin was counted as cover"


async def test_an_admin_cannot_reset_a_peer_but_can_reset_themselves(
        client, clean_db, test_urls) -> None:
    """`SW-ADR-098 (3)` and `(4)` — a Fable-5 ruling one tier above the build
    session, and the asymmetry is the whole point.

    Peer reset is a one-click takeover: hold your colleague's account and you
    hold their audit identity as well as your own. To reset a peer you demote
    them first — two deliberate, separately audited steps. Resetting YOURSELF
    takes over nothing you do not already have.
    """
    made = await _make_admin(client, clean_db, test_urls)
    b = made["B"]["id"]
    await client.post(f"/api/admin/users/{b}/role", json={"role": "admin"})

    peer = await client.post(f"/api/admin/users/{b}/reset")
    assert peer.status_code == 403, peer.text

    own = await client.post(f"/api/admin/users/{made['A']['id']}/reset")
    assert own.status_code == 200, own.text
    assert own.json()["token"]


async def test_acting_on_an_unknown_account_is_404(client, clean_db,
                                                   test_urls) -> None:
    await _make_admin(client, clean_db, test_urls)
    for path, body in (("revoke-sessions", None), ("active", {"is_active": False}),
                       ("role", {"role": "user"}), ("reset", None)):
        r = await client.post(f"/api/admin/users/999999/{path}",
                              **({"json": body} if body else {}))
        assert r.status_code == 404, f"{path} -> {r.status_code}"


# ── the overview ───────────────────────────────────────────────────────────
async def test_the_overview_counts_accounts_and_never_money(client, clean_db,
                                                            test_urls) -> None:
    made = await _make_admin(client, clean_db, test_urls)
    r = await client.get("/api/admin/overview")
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["accounts_total"] == 2
    assert body["accounts_active"] == 2
    assert body["admins"] == 1
    assert body["sessions_live"] >= 1
    # SIX expenses across both people — a COUNT of rows, which is the only
    # aggregate `admin_expense_stats` can produce.
    assert body["expenses_recorded"] == 6
    assert sum(d["count"] for d in body["signups"]) == 2

    for amount in ("379049", "3790.49", "125000", "504049"):
        assert amount not in r.text, f"the overview leaked {amount}"
