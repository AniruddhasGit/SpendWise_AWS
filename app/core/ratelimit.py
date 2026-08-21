"""Rate limits, with numbers — `E1-S6`, implementing `SW-ADR-128`.

Until this module existed **every authentication endpoint in this application
was unthrottled**: register, login and reset-redeem were all brute-forceable at
whatever rate a network link allowed. The numbers were ruled on 2026-08-05 and
nothing carried them into code.

## The arithmetic, and why two acceptance criteria look like they disagree

`E1-S6` asks for the **11th** sign-in in a minute to fail, and separately that
**each configured value is half its stated effective value**. Both are true at
once only if the divisor is real:

    per_process = ceil(effective / workers)

The store is in-process (below), so N workers hold N independent counters and a
limit configured at 5 admits 10 in aggregate. `SW-ADR-128` therefore states its
numbers as EFFECTIVE and configures each at half, for the two-worker topology
`SW-ADR-014` deploys. Run one worker — a test — and configured equals effective,
so the eleventh attempt is the one refused. **A literal 5 would satisfy the
second criterion and fail the first; a literal 10 would do the reverse.** That is
why the worker count is a setting and not a comment.

## Why `limits` and not `slowapi`'s decorators

`SRC-001 §10.9` says "`slowapi` is fine for this" — permission, not a mandate —
and `SW-ADR-128` reasons about slowapi's per-process store. This module uses
**`limits`**, which is the engine slowapi is a decorator layer over, and keeps
the same `MemoryStorage`, so every word of that ADR's accepted weakness still
holds exactly. Recorded as one `[JUDGMENT CALL]` under `SW-ADR-015`, for three
reasons the decorator form could not meet without fighting it:

* **Dual keying.** Login is limited per IP *and* per normalised email. A
  slowapi `key_func` receives only the request, and the email lives in a parsed
  body — reachable here by declaring the model in a dependency, which FastAPI
  then parses once and shares.
* **The closed envelope.** `SW-ADR-051` allows exactly one error shape and the
  code list is closed. slowapi raises its own exception with its own body.
* **`Retry-After`.** `SW-ADR-128` requires it. It comes from the window's reset
  time, which `limits` exposes and the decorator hides.

## Accepted knowingly, do not "fix"

The store resets on restart and multiplies by task count if the client ever
scales out. `SW-ADR-128` recorded that rather than fixing it: a shared store
needs Redis, Redis needs a billable service, and `SW-ADR-014` forbids one.
"""
from __future__ import annotations

import math
import time
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from limits import RateLimitItemPerDay, RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from app.core.errors import ApiError, envelope
from app.core.settings import get_settings

# One process-wide store. A moving window rather than a fixed one: a fixed
# window lets an attacker send the whole allowance in the last instant of one
# window and the whole allowance again in the first instant of the next, which
# is twice the ruled rate at the moment it matters most.
_storage = MemoryStorage()
_limiter = MovingWindowRateLimiter(_storage)


def per_process(effective: int, workers: int) -> int:
    """The number handed to the limiter, given the number that was ruled.

    **Ceiling, not floor, and this is checked rather than chosen.** `SW-ADR-128`
    states seven (effective, configured) pairs. Ceiling reproduces all seven;
    floor reproduces six and gets registration wrong — `5 // 2 == 2` where the
    ADR says 3. `test_ac5_the_arithmetic_reproduces_the_adrs_own_table` asserts
    against that table, so the rounding rule is derived from the ruling instead
    of being a preference someone typed.

    The cost is recorded rather than smoothed: for an odd numerator the effective
    limit lands slightly ABOVE the ruled one (5/min configures 3, so two workers
    admit 6). The ADR rounded in the permissive direction on purpose — a limit
    stricter than the one ruled locks out people the ruling meant to admit, and
    that failure is invisible until a real person is refused.

    `max(1, ...)` is not defensive noise either. Ceiling protects the common
    case, but a caller passing workers > effective would still reach zero
    without it — and an item of zero refuses the *first* request, turning a
    throttle into a total outage the moment someone scales out.
    """
    if workers < 1:
        raise ValueError("workers must be >= 1")
    return max(1, math.ceil(effective / workers))


def reset_all_buckets() -> None:
    """Empty every counter. For tests only.

    The store is process-global by design, which is what makes it free and what
    makes it leak between test cases: without this, the second test in a file
    starts at whatever count the first one left behind.
    """
    _storage.reset()


def client_ip(request: Request) -> str:
    """The socket address, and **only** the socket address.

    `X-Forwarded-For` is deliberately not consulted. `SW-ADR-014` left this
    deployment with no load balancer, so no proxy sits in front of the app and
    no trusted party sets that header — which means honouring it would let any
    client choose its own bucket by typing one header, and every per-IP limit
    in this module would become decorative while still reporting success.
    `GOTCHAS.md` records the mirror-image trap (trusting the socket *behind* a
    proxy limits the proxy). **If an ALB is ever introduced this becomes wrong
    in the other direction and must be revisited** — `SW-ADR-014` is the record
    to check.
    """
    return request.client.host if request.client else "unknown"


def _enforce(bucket: str, key: str, effective: int, period: str) -> None:
    """Count one attempt against `bucket:key`, or raise the 429.

    Counting happens whatever the request's eventual outcome. **A failed sign-in
    must count** — an attacker guessing passwords is, by definition, producing
    nothing but failures, so a limiter that only counted successes would let the
    attack through untouched and throttle the legitimate user who mistyped once.
    """
    s = get_settings()
    if not s.RATE_LIMIT_ENABLED:
        return
    n = per_process(effective, s.UVICORN_WORKERS)
    item = (RateLimitItemPerDay(n) if period == "day" else RateLimitItemPerMinute(n))
    identifier = f"{bucket}:{key}"
    if _limiter.hit(item, identifier):
        return
    stats = _limiter.get_window_stats(item, identifier)
    retry_after = max(1, math.ceil(stats.reset_time - time.time()))
    raise ApiError("RATE_LIMITED", headers={"Retry-After": str(retry_after)})


def _norm_email(value: object) -> str:
    """`E1-S2` ruled identity case-insensitive, so the bucket is too. Keyed on
    the raw string, `Victim@x.com` and `victim@x.com` would carry separate
    allowances — a bypass that costs an attacker one shift key."""
    return str(value or "").strip().lower()


# ── the four limited entry points ────────────────────────────────────────────
#
# Declared as dependencies rather than middleware so each carries the numbers it
# was ruled with, at the route it guards, where a reader looking at the endpoint
# can see them.

async def limit_login(request: Request) -> None:
    """10/min per IP **and** 10/min per normalised email (`SW-ADR-128`).

    Per-IP alone is bypassed by anyone with ten addresses, which is what a
    botnet is. Per-email alone lets one host work through a list of accounts at
    ten attempts each. Neither key is sufficient and the ADR requires both.
    """
    s = get_settings()
    _enforce("login-ip", client_ip(request), s.RATE_LIMIT_LOGIN_PER_MIN, "minute")
    email = ""
    try:
        body = await request.json()
        email = _norm_email(body.get("email") if isinstance(body, dict) else "")
    except Exception:                                       # noqa: BLE001
        # A malformed body is about to be rejected as a 422 anyway. It has
        # already been counted against the IP above, so a flood of unparseable
        # bodies cannot be used to avoid the limit.
        return
    if email:
        _enforce("login-email", email, s.RATE_LIMIT_LOGIN_EMAIL_PER_MIN, "minute")


async def limit_register(request: Request) -> None:
    """5/min and 20/day per IP (`SW-ADR-128`).

    Two windows, because the per-minute limit alone permits 7,200 accounts a
    day from one address — patient rather than prevented.
    """
    s = get_settings()
    ip = client_ip(request)
    _enforce("register-ip-min", ip, s.RATE_LIMIT_REGISTER_PER_MIN, "minute")
    _enforce("register-ip-day", ip, s.RATE_LIMIT_REGISTER_PER_DAY, "day")


async def limit_reset(request: Request) -> None:
    """6/min per IP (`SW-ADR-128`).

    The tightest of the three. A reset token is a bearer credential with a
    one-hour life (`SRC-001 §10.7`), so this is the endpoint where guessing pays
    best and is therefore limited hardest — which is what `SRC-001 §10.9` asks
    for by name.
    """
    _enforce("reset-ip", client_ip(request),
             get_settings().RATE_LIMIT_RESET_PER_MIN, "minute")


# Applied as `dependencies=[Depends(...)]` on the ROUTE, never as a parameter.
# FastAPI solves route-level dependencies before the endpoint's own, so a
# throttled request is refused before `get_db` runs and never opens a session —
# which is the difference between a limiter that saves the database and one that
# merely reports on it. Declared as a parameter it sat AFTER `db` in the
# signature, and every throttled request still checked out a connection first.
# Same shape as `require_admin` on the admin router (`E4-S1`).

# ── everything else ──────────────────────────────────────────────────────────

# The four auth routes carry their own, tighter limits above. Applying the
# general limit to them as well would mean a login attempt counted twice, and
# the tighter number would stop being the one that governs.
_SELF_LIMITED = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/reset/complete",
}


async def general_limit_middleware(request: Request, call_next):
    """120/min per authenticated user, 60/min per IP unauthenticated
    (`SW-ADR-128`). **Static assets are never limited.**

    Static is exempt because one dashboard load is one document plus a JS bundle
    plus a CSS bundle plus every font file, and a person who reloads twice would
    otherwise spend a visible fraction of a limit meant to govern API calls. The
    exemption is by path prefix: anything not under `/api/` is the SPA or its
    assets (`SW-ADR-020` — one container serves both).

    Keyed on the user id where there is one, so a household behind one NAT
    address is not one bucket. The id comes from the signed token, which is why
    a forged cookie cannot claim someone else's allowance: an unreadable token
    falls through to the IP key rather than being trusted.
    """
    path = request.url.path
    if not path.startswith("/api/") or path in _SELF_LIMITED:
        return await call_next(request)

    s = get_settings()
    if not s.RATE_LIMIT_ENABLED:
        return await call_next(request)

    user_id = _user_id_from_cookie(request)
    try:
        if user_id is not None:
            _enforce("api-user", str(user_id), s.RATE_LIMIT_API_USER_PER_MIN, "minute")
        else:
            _enforce("api-ip", client_ip(request), s.RATE_LIMIT_API_IP_PER_MIN, "minute")
    except ApiError as exc:
        # Middleware sits OUTSIDE the exception handlers the app installs, so
        # raising here would escape as an unhandled 500 and the envelope
        # `SW-ADR-051` mandates would never be built. Render it here instead.
        return JSONResponse(
            status_code=exc.status, content=envelope(exc),
            headers={"Cache-Control": "no-store", **exc.headers})
    return await call_next(request)


def _user_id_from_cookie(request: Request) -> int | None:
    """The signed `sub`, or None. Never raises.

    An expired, forged or malformed token is not an error here — it is simply
    not an identity, and the request falls back to the IP bucket. Treating it as
    an error would make the rate limiter a second, weaker authenticator with its
    own opinion about who you are.
    """
    from app.modules.auth.service import COOKIE_NAME
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        from app.core.security import read_token
        return int(read_token(raw).sub)
    except Exception:                                       # noqa: BLE001
        return None
