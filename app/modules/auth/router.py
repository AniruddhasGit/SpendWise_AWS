"""HTTP only. Parses, delegates, serialises. Never writes a query."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db, set_request_identity
from app.core.deps import CurrentUser, Db
from app.core.settings import get_settings
from app.modules.auth.schemas import LoginRequest, Principal, RegisterRequest
from app.modules.auth.service import ABSOLUTE_LIFETIME, COOKIE_NAME, AuthService

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


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Principal)
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


@router.post("/login", response_model=Principal)
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
