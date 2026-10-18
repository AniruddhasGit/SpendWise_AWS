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
    # Unit-test the middleware directly: an /api/ response must be no-store.
    # Hitting a real /api route would open a DB connection in its dependency,
    # which the no-database CI job cannot provide, so test the rule itself.
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    from app.core.headers import security_headers_middleware

    scope = {"type": "http", "method": "GET", "path": "/api/auth/me",
             "headers": [], "query_string": b""}

    async def call_next(_req):
        return JSONResponse({"ok": True})

    resp = await security_headers_middleware(Request(scope), call_next)
    assert resp.headers.get("cache-control") == "no-store"
    assert "content-security-policy" in resp.headers


async def test_non_api_response_is_not_forced_no_store():
    # The no-store rule is scoped to /api/; a static/SPA path keeps its own
    # caching decision.
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    from app.core.headers import security_headers_middleware

    scope = {"type": "http", "method": "GET", "path": "/assets/app.js",
             "headers": [], "query_string": b""}

    async def call_next(_req):
        return JSONResponse({"ok": True}, headers={"Cache-Control": "max-age=31536000"})

    resp = await security_headers_middleware(Request(scope), call_next)
    assert resp.headers.get("cache-control") == "max-age=31536000"


async def test_openapi_is_not_public_by_default():
    # LOG_LEVEL defaults to INFO, so the schema route is not registered. The path
    # then falls through — to the SPA shell where the client is built, or to a
    # generic error where it is not (as in the no-database CI job, which has no
    # dist). Either way the OpenAPI schema itself is never served; assert on the
    # body so the result does not depend on which fallback answered.
    from app.main import app as _app
    assert _app.openapi_url is None  # the route is simply not mounted at INFO

    r = await _get("/openapi.json")
    assert '"openapi"' not in r.text
    assert '"paths"' not in r.text
