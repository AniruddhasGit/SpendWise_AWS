"""`E1-S6` — rate limits, with numbers. The five acceptance criteria, and the
arithmetic that makes two of them stop contradicting each other.

**These tests need no database.** That is a property of the thing under test,
not a convenience: a limiter that reaches the database before it decides is
useless under exactly the load it exists to survive. `get_db` is overridden with
a stub that COUNTS its calls, and AC1 asserts the counter stops advancing at the
moment the 429 starts — so a limiter that refused correctly but only after
opening a session would fail here rather than pass more slowly.

The first ten attempts are allowed to fail however they like — wrong password,
no such account, stubbed session. What is asserted is that none of them is a
429 and the eleventh is. **Failed attempts must count**, or the limit protects
nothing: an attacker guessing passwords is, by definition, only making failures.
"""
from __future__ import annotations

import httpx
import pytest

from app.core.errors import ApiError

from app.core.ratelimit import per_process, reset_all_buckets

pytestmark = pytest.mark.asyncio


# ── the harness ──────────────────────────────────────────────────────────────

DB_HITS: list[str] = []


def _app():
    """A fresh app with the limiter ON, one worker, and a COUNTED database stub.

    An *allowed* request must reach the database — that is what being allowed
    means. A *throttled* one must not. So the stub records each call instead of
    forbidding them, and the tests assert the counter stops advancing at the
    moment the 429 starts. That is the real property: the limiter decides before
    the query, so an attack costs connections it never gets to open.

    `RATE_LIMIT_ENABLED` defaults on in production and is turned OFF by the
    shared `client` fixture, so the rest of the suite can sign in more than ten
    times a minute without failing for a reason unrelated to what it tests.
    """
    import app.main as main
    from app.core.db import get_db

    async def _counted_db():
        DB_HITS.append("hit")
        # A controlled failure. The point of these cases is the gate in front of
        # the handler, not the handler — but it has to fail as a REAL response
        # rather than an exception, or the 429 cases never get to run.
        raise ApiError("INTERNAL")

    main.app.dependency_overrides[get_db] = _counted_db
    return main.app


def _client(app, ip: str = "203.0.113.7") -> httpx.AsyncClient:
    """A client whose socket address is `ip`.

    ASGITransport's `client` tuple is what `request.client.host` reads, which is
    the only thing the IP key trusts — `X-Forwarded-For` is deliberately NOT
    consulted (`GOAL_15`, and see `test_forwarded_for_cannot_move_the_bucket`).

    `raise_app_exceptions=False` so a handler failure becomes a 500 response the
    way it would in production, instead of propagating into the test and hiding
    the status code the assertion is about.
    """
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(ip, 51234),
                                      raise_app_exceptions=False),
        base_url="http://testserver")


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    """One worker, limiter on, and every bucket emptied between cases.

    Without the reset the second test in the file starts at whatever count the
    first one left behind — the in-process store is process-global by design
    (`SW-ADR-128`), which is exactly what makes it cheap and exactly what makes
    it leak across tests.
    """
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("UVICORN_WORKERS", "1")
    monkeypatch.setenv("SPENDWISE_DOTENV", "0")
    for k, v in _REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)
    from app.core.settings import get_settings
    get_settings.cache_clear()
    reset_all_buckets()
    DB_HITS.clear()
    yield
    import app.main as main
    main.app.dependency_overrides.clear()
    get_settings.cache_clear()
    reset_all_buckets()


_REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://u:p@127.0.0.1:5432/spendwise",
    "MIGRATION_DATABASE_URL": "postgresql+asyncpg://o:p@127.0.0.1:5432/spendwise",
    "JWT_SECRET": "x" * 40,
}


def _login(email: str = "someone@spendwise.app") -> dict:
    return {"email": email, "password": "not-the-right-one"}


async def _hammer(client: httpx.AsyncClient, path: str, body_for, n: int) -> list[int]:
    out = []
    for i in range(n):
        r = await client.post(path, json=body_for(i))
        out.append(r.status_code)
    return out


# ── AC1 ──────────────────────────────────────────────────────────────────────

async def test_ac1_the_11th_signin_in_a_minute_from_one_ip_is_429_with_retry_after():
    app = _app()
    async with _client(app) as c:
        codes = await _hammer(c, "/api/auth/login", lambda i: _login(f"a{i}@x.com"), 10)
        assert 429 not in codes, (
            f"a limit fired inside the first ten attempts: {codes}. The effective "
            f"limit is 10/min and the test runs one worker, so ten must pass the gate")
        eleventh = await c.post("/api/auth/login", json=_login("a11@x.com"))

    assert eleventh.status_code == 429
    assert eleventh.headers.get("retry-after"), \
        "SW-ADR-128 requires Retry-After on the 429; without it a client has no " \
        "way to back off except by guessing"
    assert int(eleventh.headers["retry-after"]) >= 1
    assert eleventh.json()["error"]["code"] == "RATE_LIMITED"
    # The property that makes this limiter worth having: the refused request
    # never opened a database session. Ten allowed attempts reached the stub;
    # the eleventh did not. It is declared as a ROUTE-LEVEL dependency precisely
    # so FastAPI solves it before `get_db` — as an endpoint parameter it sat
    # after `db` in the signature, and every throttled request checked out a
    # connection before being refused. This assertion is what caught that.
    assert len(DB_HITS) == 10, (
        f"{len(DB_HITS)} requests reached the database across 11 attempts — the "
        f"limiter is deciding after the query rather than before it")


# ── AC2 ──────────────────────────────────────────────────────────────────────

async def test_ac2_the_11th_signin_against_one_email_from_different_ips_is_429():
    """The dual key. Ten different source addresses, one target account.

    Per-IP alone is bypassed by anyone with ten addresses, which is the whole
    point of a botnet. `SW-ADR-128` keys login twice for this reason.
    """
    app = _app()
    target = "victim@spendwise.app"
    codes = []
    for i in range(10):
        async with _client(app, ip=f"198.51.100.{i + 1}") as c:
            codes.append((await c.post("/api/auth/login", json=_login(target))).status_code)
    assert 429 not in codes, f"fired early across distinct IPs: {codes}"

    async with _client(app, ip="198.51.100.200") as c:
        eleventh = await c.post("/api/auth/login", json=_login(target))
    assert eleventh.status_code == 429
    assert eleventh.json()["error"]["code"] == "RATE_LIMITED"


async def test_ac2_the_email_key_is_case_insensitive():
    """`E1-S2` ruled identity case-insensitive. A bucket keyed on the raw string
    would give `Victim@x.com` and `victim@x.com` separate allowances — a bypass
    that costs an attacker one shift key."""
    app = _app()
    for i in range(10):
        async with _client(app, ip=f"198.51.100.{i + 1}") as c:
            await c.post("/api/auth/login", json=_login("Victim@Spendwise.App"))
    async with _client(app, ip="198.51.100.201") as c:
        r = await c.post("/api/auth/login", json=_login("victim@spendwise.app"))
    assert r.status_code == 429, "case variation opened a fresh bucket"


async def test_a_different_email_from_a_fresh_ip_is_not_punished():
    """The limit must not become a denial of service against everyone else.
    One hammered account cannot lock out an unrelated person on another IP."""
    app = _app()
    for i in range(10):
        async with _client(app, ip=f"198.51.100.{i + 1}") as c:
            await c.post("/api/auth/login", json=_login("victim@spendwise.app"))
    async with _client(app, ip="192.0.2.55") as c:
        r = await c.post("/api/auth/login", json=_login("bystander@spendwise.app"))
    assert r.status_code != 429


# ── AC3 ──────────────────────────────────────────────────────────────────────

async def test_ac3_the_6th_registration_in_a_minute_from_one_ip_is_429():
    app = _app()
    def body(i):
        return {"email": f"new{i}@spendwise.app", "password": "a-long-enough-one",
                "display_name": f"New {i}"}
    async with _client(app, ip="203.0.113.44") as c:
        codes = await _hammer(c, "/api/auth/register", body, 5)
        assert 429 not in codes, f"fired inside the first five: {codes}"
        sixth = await c.post("/api/auth/register", json=body(99))
    assert sixth.status_code == 429
    assert sixth.headers.get("retry-after")
    assert sixth.json()["error"]["code"] == "RATE_LIMITED"


# ── AC4 ──────────────────────────────────────────────────────────────────────

async def test_ac4_the_7th_reset_redemption_in_a_minute_from_one_ip_is_429():
    app = _app()
    def body(i):
        return {"token": f"guess-{i}", "new_password": "a-long-enough-one"}
    async with _client(app, ip="203.0.113.90") as c:
        codes = await _hammer(c, "/api/auth/reset/complete", body, 6)
        assert 429 not in codes, f"fired inside the first six: {codes}"
        seventh = await c.post("/api/auth/reset/complete", json=body(99))
    assert seventh.status_code == 429
    assert seventh.json()["error"]["code"] == "RATE_LIMITED"


# ── AC5 ──────────────────────────────────────────────────────────────────────

def test_ac5_the_arithmetic_reproduces_the_adrs_own_table():
    """The arithmetic, asserted against `SW-ADR-128`'s stated pairs rather than
    against a rounding rule someone preferred.

    The ADR gives seven (effective, configured) pairs for the two-worker
    topology. Ceiling division reproduces all seven. Floor reproduces six and
    gets registration wrong — `5 // 2 == 2` where the ADR says **3** — which is
    how the first version of this module was wrong, and how this test caught it.
    """
    ADR_128 = [(10, 5),    # login per IP
               (10, 5),    # login per email
               (5, 3),     # registration per minute  <- the one floor gets wrong
               (20, 10),   # registration per day
               (6, 3),     # reset completion
               (120, 60),  # everything else, per user
               (60, 30)]   # everything else, per IP
    for effective, configured in ADR_128:
        assert per_process(effective, workers=2) == configured, (
            f"{effective}/min at 2 workers should configure {configured} per "
            f"process, per SW-ADR-128")


def test_ac5_rounding_never_ships_a_limit_stricter_than_the_one_ruled():
    """The direction of the rounding error matters and was chosen, not inherited.

    Ceiling can admit slightly more than ruled (5 configures 3, so two workers
    admit 6). Floor would admit less (2 → 4 < 5). A limit looser than ruled costs
    an attacker a little time; a limit stricter than ruled refuses real people,
    and nothing in the system reports that it happened.
    """
    for effective in (5, 7, 9, 11, 25):
        assert per_process(effective, workers=2) * 2 >= effective


def test_ac5_one_worker_means_configured_equals_effective():
    """Which is why AC1 says the ELEVENTH attempt and AC5 says half: the tests
    run one process. A literal 5 would satisfy AC5 and fail AC1."""
    for effective in (10, 6, 5, 20):
        assert per_process(effective, workers=1) == effective


def test_ac5_a_limit_never_rounds_down_to_zero():
    """`1 // 4 == 0`, and a limit of zero refuses the first request — turning a
    throttle into an outage the moment someone scales out."""
    assert per_process(1, workers=4) == 1
    assert per_process(3, workers=8) == 1


def test_ac5_the_ruled_numbers_are_the_ones_configured():
    """`SW-ADR-128`'s numbers, read from settings rather than restated here —
    a test that repeats the literals cannot detect them being changed."""
    from app.core.settings import get_settings
    s = get_settings()
    assert s.RATE_LIMIT_LOGIN_PER_MIN == 10
    assert s.RATE_LIMIT_LOGIN_EMAIL_PER_MIN == 10
    assert s.RATE_LIMIT_REGISTER_PER_MIN == 5
    assert s.RATE_LIMIT_REGISTER_PER_DAY == 20
    assert s.RATE_LIMIT_RESET_PER_MIN == 6
    assert s.RATE_LIMIT_API_USER_PER_MIN == 120
    assert s.RATE_LIMIT_API_IP_PER_MIN == 60


# ── the trap GOTCHAS names, asserted rather than trusted ─────────────────────

async def test_forwarded_for_cannot_move_the_bucket():
    """`GOTCHAS.md`: slowapi's default key behind a proxy limits the proxy.

    This deployment has no proxy (`SW-ADR-014` — no load balancer), so there is
    no header any trusted party sets. If `X-Forwarded-For` were honoured, every
    per-IP limit here would be bypassable by anyone willing to type a header,
    and the limiter would report success while protecting nothing.
    """
    app = _app()
    async with _client(app, ip="203.0.113.77") as c:
        for i in range(10):
            await c.post("/api/auth/login", json=_login(f"z{i}@x.com"))
        spoofed = await c.post("/api/auth/login", json=_login("z11@x.com"),
                               headers={"X-Forwarded-For": "9.9.9.9"})
    assert spoofed.status_code == 429, \
        "X-Forwarded-For opened a fresh bucket — the per-IP limit is decorative"


async def test_the_limiter_is_off_when_disabled():
    """The switch the rest of the suite depends on. If this ever stops working,
    unrelated tests start failing at their eleventh sign-in."""
    import app.main as main
    from app.core.settings import get_settings
    from app.core.db import get_db

    async def _no_db():
        raise AssertionError("unreachable")
    main.app.dependency_overrides[get_db] = _no_db

    import os
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    get_settings.cache_clear()
    reset_all_buckets()
    try:
        async with _client(main.app, ip="203.0.113.123") as c:
            codes = await _hammer(c, "/api/auth/login", lambda i: _login(f"q{i}@x.com"), 15)
        assert 429 not in codes, f"limiter fired while disabled: {codes}"
    finally:
        os.environ["RATE_LIMIT_ENABLED"] = "true"
        get_settings.cache_clear()


# ── "everything else", and the exemption that keeps it usable ────────────────

async def test_the_61st_unauthenticated_api_call_from_one_ip_is_429():
    """`SW-ADR-128`: 60/min per IP for unauthenticated API paths."""
    app = _app()
    async with _client(app, ip="203.0.113.201") as c:
        codes = [(await c.get("/api/auth/me")).status_code for _ in range(60)]
        assert 429 not in codes, f"fired inside the first sixty: {codes[:12]}"
        sixty_first = await c.get("/api/auth/me")
    assert sixty_first.status_code == 429
    assert sixty_first.json()["error"]["code"] == "RATE_LIMITED"
    assert sixty_first.headers.get("retry-after")


async def test_static_assets_are_never_limited():
    """One dashboard load is a document, a JS bundle, a CSS bundle and six font
    files. Counting those against an API limit means a person who reloads twice
    spends a meaningful fraction of it, so `SW-ADR-128` exempts static. The
    exemption has to be asserted, or the next middleware edit silently ends it.
    """
    app = _app()
    async with _client(app, ip="203.0.113.202") as c:
        codes = [(await c.get("/")).status_code for _ in range(80)]
    assert 429 not in codes, "a static path was rate limited"


async def test_the_general_limit_does_not_double_count_the_auth_routes():
    """Login carries its own tighter limit. If the general middleware counted it
    too, the effective sign-in limit would be whichever bucket filled first and
    the ruled number would stop being the one that governs."""
    app = _app()
    async with _client(app, ip="203.0.113.203") as c:
        codes = await _hammer(c, "/api/auth/login", lambda i: _login(f"m{i}@x.com"), 10)
    assert codes.count(429) == 0
    async with _client(app, ip="203.0.113.203") as c:
        r = await c.get("/api/auth/me")
    assert r.status_code != 429, "login attempts consumed the general API allowance"


async def test_a_forged_cookie_falls_back_to_the_ip_bucket():
    """An unreadable token is not an identity. If a forged cookie were trusted
    as a user id, an attacker would get a private 120/min bucket per invented
    `sub` — a LARGER allowance than an honest anonymous caller, granted for
    presenting a credential that failed to verify."""
    app = _app()
    forged = {"sw_session": "not.a.real.token"}
    async with _client(app, ip="203.0.113.204") as c:
        codes = [(await c.get("/api/auth/me", cookies=forged)).status_code
                 for _ in range(61)]
    assert codes[-1] == 429, "a forged cookie bought a larger bucket than anonymity"

