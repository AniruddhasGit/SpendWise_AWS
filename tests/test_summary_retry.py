"""The summary read retries a serialization failure transparently (the 500 the
dashboard hit under concurrent writes). Deterministic: the DB error is injected,
not raced, so the wiring — specific exception handler -> internal 503 marker ->
retry middleware replay -> stripped before the client — is what is under test.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import DBAPIError

import app.modules.expenses.service_db as service_mod
from app.core.errors import RETRYABLE_HEADER, is_serialization_failure
from app.main import app

SUMMARY = "/api/expenses/summary?from=2026-10-01&to=2026-10-31"


class _FortyThousandAndOne(Exception):
    """Stands in for asyncpg's SerializationError — same SQLSTATE."""
    sqlstate = "40001"


def _serialization_dbapi_error() -> DBAPIError:
    orig = _FortyThousandAndOne("could not serialize access due to concurrent update")
    err = DBAPIError.instance("SELECT ...", {}, orig, Exception)
    err.__cause__ = orig
    return err


def test_is_serialization_failure_walks_the_cause_chain():  # sync
    assert is_serialization_failure(_serialization_dbapi_error())
    assert not is_serialization_failure(ValueError("something else"))


async def _get_summary_as_a_logged_in_user(monkeypatch, fail_times: int):
    """Patch the summary so the first `fail_times` calls raise 40001, then it
    succeeds. Authentication is stubbed to keep this a pure wiring test with no
    database."""
    calls = {"n": 0}
    real_payload = {
        "from": "2026-10-01", "to": "2026-10-31",
        "total_paise": 0, "total": "0.00", "count": 0, "days_elapsed": 1,
        "daily_average_paise": None, "daily_average": None,
        "by_category": [], "by_day": [],
    }

    async def fake_summary(self, user_id, q):
        calls["n"] += 1
        if calls["n"] <= fail_times:
            raise _serialization_dbapi_error()
        return real_payload

    monkeypatch.setattr(service_mod.ExpenseService, "summary", fake_summary)

    # Stub auth + the session dependency so no DB is touched (the summary itself
    # is patched above).
    from app.core import deps

    class _P:
        id = 1
        role = "user"

    async def fake_user():
        return _P()

    def fake_db():
        return None

    app.dependency_overrides[deps.get_current_user_rr] = fake_user
    app.dependency_overrides[deps.db_of] = fake_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://t") as c:
            r = await c.get(SUMMARY)
        return r, calls["n"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_summary_retries_past_one_serialization_failure(monkeypatch):
    r, n = await _get_summary_as_a_logged_in_user(monkeypatch, fail_times=1)
    assert r.status_code == 200, r.text
    assert n == 2  # failed once, replayed once, succeeded
    assert RETRYABLE_HEADER not in {k.lower() for k in r.headers}


@pytest.mark.asyncio
async def test_summary_gives_up_as_an_opaque_500_never_leaking_the_marker(monkeypatch):
    r, n = await _get_summary_as_a_logged_in_user(monkeypatch, fail_times=99)
    assert r.status_code == 500
    assert r.json() == {"error": {"code": "INTERNAL", "message": "Something went wrong."}}
    assert RETRYABLE_HEADER not in {k.lower() for k in r.headers}
    assert n == 3  # the original try plus two replays, then it stops
