"""FastAPI dependencies. Written ONCE and applied to whole routers.

`SRC-001 §4.3`: one place, never a check copy-pasted per handler. A per-handler
check is one handler away from being forgotten, and the forgetting is silent.

**The ordering here is the whole of `SW-ADR-136`, and it is not negotiable:**

    1. read the cookie, verify the token   -> gives us `sub`
    2. SELECT set_config('app.user_id', :sub, true)   <- FIRST STATEMENT
    3. only now, SELECT the session row

`sessions` is under FORCE ROW LEVEL SECURITY with a policy keyed on
`app.user_id`. Do step 3 before step 2 and `current_setting(…, true)` is NULL,
the predicate is NULL, and the lookup returns **zero rows for every request ever
made** — authentication that never succeeds, with no error to explain it.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Cookie, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, get_db_rr, set_request_identity
from app.core.errors import ApiError
from app.modules.auth.schemas import Principal
from app.modules.auth.service import COOKIE_NAME, AuthService, read_claims


async def _principal(request: Request, db: AsyncSession, token: str | None) -> Principal:
    if not token:
        raise ApiError("UNAUTHENTICATED")

    claims = read_claims(token)                       # step 1
    await set_request_identity(db, claims.sub)        # step 2 — FIRST statement
    principal = await AuthService(db).principal_for(claims)   # step 3

    # Stashed so a handler can revoke THIS session on sign-out without decoding
    # the token a second time.
    request.state.session_id = claims.jti
    return principal


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    sw_session: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> Principal:
    return await _principal(request, db, sw_session)


async def get_current_user_rr(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_rr)],
    sw_session: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> Principal:
    """Same identity, REPEATABLE READ session — for the summary, whose three
    aggregates must agree with each other (`SW-ADR-142 F`)."""
    return await _principal(request, db, sw_session)


async def require_admin(
    principal: Annotated[Principal, Depends(get_current_user)],
) -> Principal:
    """Applied as `dependencies=[Depends(require_admin)]` on the WHOLE admin
    router — one place, never per handler."""
    if principal.role != "admin":
        raise ApiError("FORBIDDEN")
    return principal


def db_of(request: Request) -> AsyncSession:
    """The one session for this request, from `request.state`.

    Handlers take this rather than declaring a second session dependency —
    declaring one would open a SECOND transaction, which carries no
    `app.user_id` and returns zero rows everywhere (`SW-ADR-144 A`).
    """
    db = getattr(request.state, "db", None)
    if db is None:                                     # pragma: no cover
        raise RuntimeError("no session on this request — an auth dependency must run first")
    return db


CurrentUser = Annotated[Principal, Depends(get_current_user)]
CurrentUserRR = Annotated[Principal, Depends(get_current_user_rr)]
AdminUser = Annotated[Principal, Depends(require_admin)]
Db = Annotated[AsyncSession, Depends(db_of)]
