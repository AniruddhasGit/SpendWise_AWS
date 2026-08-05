"""E0-S10 — `/healthz`, `/readyz`, and the catch-all that must not swallow 404s.

The two probes answer different questions, and the tests that matter are the
ones proving they are still different: a `/healthz` that touches the database
gets a container killed by an RDS blip, and a `/readyz` that does not touch it
reports ready while nothing works.
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.db]


async def test_healthz_is_200_with_no_body(client, clean_db) -> None:
    """`P-OPS-03` AC1: bodiless. `null` is a body — the container health check
    parses what it gets, and `null` is JSON."""
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.content == b""
    assert r.headers["cache-control"] == "no-store"


async def test_healthz_does_not_touch_the_database(client, clean_db, monkeypatch) -> None:
    """The criterion, ASSERTED rather than asserted about.

    The session factory is replaced with one that raises. `/healthz` must still
    answer 200 — if it acquires a session at all, this fails. `/readyz` in the
    next test proves the sabotage would have been caught.
    """
    import app.core.db as db_mod

    def explode(*a, **kw):
        raise AssertionError("/healthz opened a database session")

    monkeypatch.setattr(db_mod, "_session_for", explode)
    r = await client.get("/healthz")
    assert r.status_code == 200


async def test_the_sabotage_in_the_previous_test_really_would_break_readyz(
        client, clean_db, monkeypatch) -> None:
    """The red-proof for it. Without this, the test above passes just as well
    against a `_session_for` that is never called by anything."""
    import app.core.db as db_mod

    real = db_mod._session_for
    calls = []
    def counted(*a, **kw):
        calls.append(1)
        return real(*a, **kw)

    monkeypatch.setattr(db_mod, "_session_for", counted)
    assert (await client.get("/readyz")).status_code in (200, 503)
    assert calls, "/readyz did not open a session either — the probe above proves nothing"


async def test_readyz_reports_status_revision_and_build(client, clean_db) -> None:
    """AC2. The revision comes from `alembic_version`, not from a constant
    compiled into the image — `SW-ADR-093` runs migrations at container start,
    so "built with" and "running" are different questions."""
    r = await client.get("/readyz")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ready"
    assert body["revision"], "no migration revision — is the test database migrated?"
    assert "build" in body
    assert r.headers["cache-control"] == "no-store"


async def test_readyz_is_503_when_the_database_is_unreachable(client, clean_db,
                                                              monkeypatch) -> None:
    """A readiness probe returning 200 while the database is down has answered
    the question `/healthz` asks, not the one it was asked."""
    from sqlalchemy.ext.asyncio import AsyncSession

    async def explode(self, *a, **kw):
        raise ConnectionError("simulated: RDS unreachable")

    monkeypatch.setattr(AsyncSession, "execute", explode)
    r = await client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not ready"
    assert body["reason"] == "ConnectionError"


async def test_readyz_never_leaks_the_connection_string(client, clean_db,
                                                        monkeypatch) -> None:
    """It is unauthenticated. A driver's error text carries the host, the port,
    the database and sometimes the user — so the TYPE is reported, never the
    message (`SW-ADR-051`'s no-detail rule, for the same reason)."""
    from sqlalchemy.ext.asyncio import AsyncSession

    async def explode(self, *a, **kw):
        raise ConnectionError(
            "could not connect to spend-wise-dev-db.example.rds.amazonaws.com:5432 "
            "user=spendwise_app password=hunter2")

    monkeypatch.setattr(AsyncSession, "execute", explode)
    text = (await client.get("/readyz")).text
    for secret in ("rds.amazonaws.com", "spendwise_app", "hunter2", "5432"):
        assert secret not in text, f"/readyz leaked {secret!r}"


async def test_an_unknown_api_path_is_a_404_envelope_not_index_html(client,
                                                                    clean_db) -> None:
    """**The reason the catch-all is mounted last.**

    A catch-all registered before the API routers returns index.html with a
    200, so a client calling a misspelt endpoint parses HTML as JSON and
    reports a syntax error at character 0 instead of a 404.
    """
    r = await client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/json")
    assert r.json()["error"]["code"] == "NOT_FOUND"
    assert "<!doctype" not in r.text.lower()


async def test_an_unknown_page_path_returns_the_client_shell(client, clean_db) -> None:
    """`SW-ADR-020`: the client owns its own routing, so an unknown page path
    is the shell, not a 404. Skipped rather than failed when `dist/` is absent
    — the API is legitimately runnable without the frontend toolchain."""
    from app.core.spa import DIST

    if not (DIST / "index.html").is_file():
        pytest.skip("client/dist is not built")

    r = await client.get("/anything/at/all")
    assert r.status_code == 200
    assert "<!doctype html>" in r.text.lower()
    assert r.headers["cache-control"] == "no-store", (
        "a cached shell names the previous deploy's hashed assets, which is a "
        "blank page that clears on a hard refresh and on nothing else")
