"""`range.required` — specified since the contract was written, unimplemented
until now, and carried in two handovers as a known defect.

The contract is unambiguous (`error_codes.precedence.scope.range_required`):

> A missing `from` or `to` is `range.required`, with `field` set to the key that
> is actually missing — **not** `field.required`, which would otherwise make
> `range.required` unreachable (G2).

and rule 11 fixes the tie:

> field: `<from or to, whichever is missing; ``from`` when BOTH are absent>`
> message: "Both from and to are required; there is no default range."

Both endpoints declared `from` and `to` as REQUIRED query parameters, so FastAPI
rejected the request before any rule in this system ran, and every caller got
`field.required`. The contract calls that outcome out by name — it is the exact
condition under which `range.required` becomes dead text, and a rule that can
never fire is the same defect as a missing one.

**Why this survived a suite of 224 tests.** There was a test. It asserted the
person's endpoint and the administrator's endpoint answer *identically* — and
they did, because both were wrong in the same way. A consistency assertion over
two callers of one broken helper is a test that can only fail if someone fixes
exactly one of them. It is strengthened below to assert the code, not just the
agreement.

These tests need no database: the refusal happens during request validation,
before the handler and before any session.
"""
from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.asyncio

_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://u:p@db.invalid:5432/spendwise",
    "MIGRATION_DATABASE_URL": "postgresql+asyncpg://o:p@db.invalid:5432/spendwise",
    "JWT_SECRET": "x" * 40,
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SPENDWISE_DOTENV", "0")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    for k, v in _ENV.items():
        monkeypatch.setenv(k, v)
    from app.core.settings import get_settings
    get_settings.cache_clear()
    yield
    import app.main as main
    main.app.dependency_overrides.clear()
    get_settings.cache_clear()


def _app():
    """The app with authentication and the database stubbed out.

    `range.required` is a *validation* outcome. Requiring a signed-in person and
    a live database to observe it would make this test unrunnable on a bare
    clone for no gain — and would have hidden the defect behind two other
    prerequisites, which is roughly how it stayed hidden this long.
    """
    import app.main as main
    from app.core.deps import db_of, get_current_user, get_current_user_rr
    from app.modules.auth.schemas import Principal

    async def _null_db():
        # Yields rather than raises. A stub that raises fires DURING dependency
        # resolution, which happens before FastAPI reports the missing query
        # parameters — so every case came back 500 and the thing under test
        # never ran. Passive is the only stub that leaves validation visible.
        yield None

    def _fake_principal():
        return Principal(id=1, email="a@spendwise.app", display_name="A",
                         role="admin", currency="INR", is_active=True,
                         receipts_enabled=False)

    main.app.dependency_overrides[db_of] = _null_db
    main.app.dependency_overrides[get_current_user] = _fake_principal
    main.app.dependency_overrides[get_current_user_rr] = _fake_principal
    return main.app


def _client(app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver")


SUMMARY = "/api/expenses/summary"
SPENDING = "/api/admin/users/2/spending"

# (query string, the field the contract says must be reported)
CASES = [
    pytest.param("", "from", id="both-absent-reports-from"),
    pytest.param("?to=2026-08-31", "from", id="from-absent"),
    pytest.param("?from=2026-08-01", "to", id="to-absent"),
]


@pytest.mark.parametrize("qs,expected_field", CASES)
@pytest.mark.parametrize("path", [SUMMARY, SPENDING])
async def test_a_missing_range_is_range_required_not_field_required(
        path, qs, expected_field):
    async with _client(_app()) as c:
        r = await c.get(path + qs)

    assert r.status_code == 422, r.text
    err = r.json()["error"]
    assert err["code"] == "VALIDATION_ERROR"
    assert err["message"] == "Both from and to are required; there is no default range.", (
        f"{path}{qs or ' (no params)'} answered {err['message']!r}. The contract "
        f"fixes this string; `field.required`'s message reaching here is the G2 "
        f"condition that makes range.required unreachable")
    assert err["field"] == expected_field, (
        f"reported field {err['field']!r}, contract says {expected_field!r}")


@pytest.mark.parametrize("qs,_f", CASES)
async def test_both_endpoints_still_answer_identically(qs, _f):
    """The property the pre-existing test asserted, kept — but now it is one
    assertion among several rather than the only one. On its own it passed
    while both endpoints were wrong."""
    async with _client(_app()) as c:
        own = await c.get(SUMMARY + qs)
        theirs = await c.get(SPENDING + qs)
    assert own.status_code == theirs.status_code == 422
    assert own.json() == theirs.json(), (
        "`CR-001 §2`: the same rules through the same helper")


async def test_a_complete_range_gets_past_validation():
    """The guard must not swallow valid requests. With both keys present the
    request reaches the handler — here the stubbed database, which is a 500.
    A 422 would mean the fix rejects everything."""
    async with _client(_app()) as c:
        r = await c.get(f"{SUMMARY}?from=2026-08-01&to=2026-08-31")
    assert r.status_code != 422, (
        "a complete range was rejected as invalid — the guard fires too early")


async def test_an_empty_value_is_a_missing_value():
    """`?from=&to=2026-08-31` is a present key with nothing in it.

    Treated as supplied, it reaches the date parser and reports `field.type`,
    which tells the caller their date is malformed when what they actually did
    was omit it. The distinction matters because the two have different fixes.
    """
    async with _client(_app()) as c:
        r = await c.get(f"{SUMMARY}?from=&to=2026-08-31")
    err = r.json()["error"]
    assert err["field"] == "from"
    assert err["message"] == "Both from and to are required; there is no default range."


async def test_range_required_outranks_the_other_range_rules():
    """`?from=` with a `to` that also breaks a later rule still reports the
    missing key. You cannot judge the order or the span of a range with one end
    absent, so anything that claims to has judged a range it does not have."""
    async with _client(_app()) as c:
        r = await c.get(f"{SUMMARY}?to=1999-01-01")
    err = r.json()["error"]
    assert err["field"] == "from"
    assert err["message"] == "Both from and to are required; there is no default range."
