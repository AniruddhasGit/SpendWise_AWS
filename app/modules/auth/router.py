"""HTTP only. Parses, delegates, serialises. Never writes a query."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, set_request_identity
from app.core.deps import CurrentUser, Db
from app.core.settings import get_settings
from app.core.ratelimit import limit_login, limit_register, limit_reset
from app.modules.auth.schemas import (
    LoginRequest, PasswordChange, Principal, ProfileUpdate, RegisterRequest, ResetComplete,
)
from app.modules.auth.service import (
    ABSOLUTE_LIFETIME, COOKIE_NAME, AccountService, AuthService,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    """`SRC-001 §10.4`. httpOnly so script cannot read it; SameSite=Lax so a
    cross-site form post cannot ride it; `Secure` from settings — false by
    default because `SW-ADR-014` left the deployment without TLS, which is a
    RECORDED WEAKNESS and never a default to copy."""
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True, samesite="lax", secure=get_settings().COOKIE_SECURE,
        max_age=int(ABSOLUTE_LIFETIME.total_seconds()), path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Principal,
             dependencies=[Depends(limit_register)])
async def register(body: RegisterRequest, request: Request, response: Response,
                   db: Annotated[AsyncSession, Depends(get_db)]) -> Principal:
    svc = AuthService(db)
    # The service sets the request identity itself, between creating the user
    # row and creating the eight categories — the categories policy refuses the
    # insert without it.
    user = await svc.register(email=body.email, password=body.password,
                              display_name=body.display_name)
    token = await svc.open_session(user, user_agent=request.headers.get("user-agent"),
                                   ip=request.client.host if request.client else None)
    _set_cookie(response, token)
    return svc._principal(user)


@router.post("/login", response_model=Principal,
             dependencies=[Depends(limit_login)])
async def login(body: LoginRequest, request: Request, response: Response,
                db: Annotated[AsyncSession, Depends(get_db)]) -> Principal:
    svc = AuthService(db)
    user = await svc.authenticate(email=body.email, password=body.password)
    await set_request_identity(db, user.id)
    token = await svc.open_session(user, user_agent=request.headers.get("user-agent"),
                                   ip=request.client.host if request.client else None)
    _set_cookie(response, token)
    return svc._principal(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response,
                 principal: CurrentUser, db: Db) -> None:
    """Revokes the row AND clears the cookie. Clearing the cookie alone would
    leave a token that still works if it were ever replayed (`NEG-A-03`)."""
    await AuthService(db).close_session(request.state.session_id)
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=Principal)
async def me(principal: CurrentUser) -> Principal:
    return principal


# ── the settings a person owns (SW-ADR-148) ────────────────────────────────
@router.patch("/me", response_model=Principal)
async def update_me(body: ProfileUpdate, principal: CurrentUser, db: Db) -> Principal:
    return await AccountService(db).update_profile(
        principal, display_name=body.display_name)


@router.post("/password")
async def change_password(body: PasswordChange, request: Request,
                          principal: CurrentUser, db: Db) -> dict:
    """Signs out every OTHER session, never this one."""
    revoked = await AccountService(db).change_password(
        principal, current=body.current_password, new=body.new_password,
        keep_session_id=request.state.session_id)
    return {"signed_out_elsewhere": revoked}


@router.post("/reset/complete", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[Depends(limit_reset)])
async def complete_reset(body: ResetComplete,
                         db: Annotated[AsyncSession, Depends(get_db)]) -> Response:
    """UNAUTHENTICATED by definition — the point of a reset is that the person
    cannot sign in (`SW-ADR-071`, which is why `password_resets` sits outside
    row-level security)."""
    await AccountService(db).redeem_reset(token=body.token,
                                          new_password=body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate(response: Response, principal: CurrentUser, db: Db) -> Response:
    """Deactivation, NOT deletion (`SW-ADR-148`).

    `SW-ADR-107` rules that user deletion does not exist in v1 — deleting a
    person's financial history is the clearest one-way door in the register.
    This is the reversible half: sign-in refused, every session revoked, the
    record intact and restorable by an administrator.
    """
    await AccountService(db).deactivate_self(principal)
    out = Response(status_code=status.HTTP_204_NO_CONTENT)
    out.delete_cookie(COOKIE_NAME, path="/")
    return out


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(response: Response, principal: CurrentUser, db: Db) -> Response:
    """SOFT deletion (`CR-001`, `SW-ADR-150`). The account closes; the rows stay.

    Distinct from `/deactivate` and deliberately so: deactivate is "pause me",
    this is "close it". Never label one and call the other — the client's copy
    for this control promises that sign-in is refused, that the records are
    retained, that an administrator can restore it and that the email address
    stays taken, and all four of those are only true of THIS handler.

    204 with no body, and the cookie is cleared here as well as the session rows
    being revoked in the service. Clearing the cookie alone would leave a token
    that still works if it were ever replayed (`NEG-A-03`); revoking alone would
    leave the browser holding a cookie for an account that no longer answers,
    and every subsequent request would 401 instead of reading as signed out.
    """
    await AccountService(db).delete_self(principal)
    out = Response(status_code=status.HTTP_204_NO_CONTENT)
    out.delete_cookie(COOKIE_NAME, path="/")
    return out


@router.get("/export")
async def export_me(principal: CurrentUser, db: Db) -> dict:
    """Everything this account holds, as JSON.

    Written as the counterweight to there being no deletion. `CR-001` added
    deletion and made this MORE load-bearing rather than less: the deletion is
    soft, so the rows survive where the person can no longer reach them, and the
    settings screen offers this export before it offers the delete. Leaving with
    your record is the version of leaving that stays reversible for the person
    as well as for the administrator.

    Their OWN rows only — this runs under the same row-level security as every
    other request, so it cannot return anyone else's even if the query were
    wrong.
    """
    from app.modules.categories.service import CategoryService
    from app.modules.expenses.service_db import ExpenseService

    cats = await CategoryService(db).list_for(principal.id)
    page = await ExpenseService(db).list_page(
        principal, limit=200, offset=0, from_=None, to=None, category_id=None)
    return {
        "account": principal.model_dump(),
        "categories": [{"id": c.id, "name": c.name, "color": c.color} for c in cats],
        "expenses": [e.model_dump(mode="json") for e in page["items"]],
        "note": "amount_paise is the exact integer; amount is the same value as a "
                "decimal string. The client never divides by 100.",
    }
