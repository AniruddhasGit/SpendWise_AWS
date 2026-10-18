"""F-S1/F-S3/F-S6: security headers on every response, /openapi.json gated,
the Server banner stripped. Written before the implementation (DoD).

These assert on the ASGI app directly with no database, so they run in the
no-database subset.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio


async def _get(path: str):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        return await c.get(path)


async def test_security_headers_present_on_the_spa_shell():
    r = await _get("/")
    h = r.headers
    assert "content-security-policy" in h
    csp = h["content-security-policy"]
    # scripts locked to self — the real XSS lever
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp
    assert h.get("x-content-type-options") == "nosniff"
    assert "referrer-policy" in h
    assert "permissions-policy" in h


async def test_server_banner_is_not_advertised():
    r = await _get("/")
    assert "server" not in {k.lower() for k in r.headers}


async def test_api_json_is_not_cacheable():
    # /api/auth/me is unauthenticated-safe (returns 401) but still an /api route;
    # whatever the status, it must not be cacheable.
    r = await _get("/api/auth/me")
    assert r.headers.get("cache-control") == "no-store"


async def test_openapi_is_not_public_by_default():
    # LOG_LEVEL defaults to INFO in the test settings, so the schema route is not
    # registered. The path then falls through to the SPA catch-all and returns
    # the HTML shell — never the JSON schema. The point is that the schema is not
    # served, not the exact status.
    r = await _get("/openapi.json")
    assert "application/json" not in r.headers.get("content-type", "")
    assert '"openapi"' not in r.text
    assert '"paths"' not in r.text
