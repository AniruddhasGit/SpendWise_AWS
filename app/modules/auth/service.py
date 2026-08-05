"""Registration, sign-in, sign-out, and turning a token into a principal.

The layer that translates. It calls the users and categories **services** — the
sanctioned kind of crossing — and never touches their tables directly.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import set_request_identity
from app.core.errors import ApiError
from app.core.security import (
    TokenClaims, TokenError, hash_password, mint_token, read_token, verify_password,
)
from app.core.settings import get_settings
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import Principal
from app.modules.categories.service import CategoryService
from app.modules.users.repository import UserRepository

COOKIE_NAME = "sw_session"                 # CV-01

# SW-ADR-099. An absolute cap, then an idle window that depends on the role: an
# admin session left open is a larger blast radius than a person's own.
ABSOLUTE_LIFETIME = timedelta(days=30)
IDLE_USER = timedelta(days=14)
IDLE_ADMIN = timedelta(minutes=30)


def _idle_window(role: str) -> timedelta:
    return IDLE_ADMIN if role == "admin" else IDLE_USER


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.sessions = AuthRepository(db)
        self.users = UserRepository(db)
        self.categories = CategoryService(db)

    def _principal(self, u) -> Principal:
        return Principal(
            id=u.id, email=u.email, display_name=u.display_name, role=u.role,
            currency=u.currency, is_active=u.is_active,
            receipts_enabled=get_settings().receipts_enabled,
        )

    # ── register ───────────────────────────────────────────────────────────
    async def register(self, *, email: str, password: str, display_name: str):
        """`P-ACC-01` + `P-ACC-02`.

        The bootstrap claim is evaluated **only when the administrator count is
        zero**, and only for the configured address. After the first, only an
        existing administrator promotes.
        """
        role = "user"
        if await self.users.admin_count() == 0:
            bootstrap = get_settings().BOOTSTRAP_ADMIN_EMAIL
            if bootstrap and email.strip().lower() == bootstrap.strip().lower():
                role = "admin"

        pw_hash = await hash_password(password)
        try:
            user = await self.users.create(email=email, password_hash=pw_hash,
                                           display_name=display_name, role=role)
            # THE IDENTITY MUST BE SET HERE, between the two inserts.
            #
            # `users` is outside RLS, so it inserts without one. `categories` is
            # NOT — its policy carries a WITH CHECK, and creating the eight
            # before `app.user_id` exists is refused with "new row violates
            # row-level security policy". Registration is the one path where the
            # identity is only knowable AFTER a write, which is exactly why it
            # is easy to get wrong and why RLS is the thing that catches it.
            await set_request_identity(self.db, user.id)

            # Every new account starts with the eight (P-REC-05), created in the
            # SAME transaction — a person with no categories is a broken account,
            # not one who has not got round to it yet.
            await self.categories.create_defaults(user.id)
            await self.db.flush()
        except IntegrityError as exc:
            # The unique index on lower(email) is the enforcer. A pre-read would
            # RACE: two simultaneous registrations both see "free" and both
            # insert. Catching the violation is the only correct order.
            if "uq_users_lower_email" in str(exc.orig):
                raise ApiError("EMAIL_TAKEN", field="email") from exc
            raise
        return user

    # ── sign in ────────────────────────────────────────────────────────────
    async def authenticate(self, *, email: str, password: str):
        """`P-ACC-03`.

        The password is verified **even when the email is unknown** — against a
        dummy hash — so "no such account" costs the same as "wrong password".
        Returning early is an enumeration oracle timed with a stopwatch
        (`SRC-001 §10.5`).
        """
        user = await self.users.by_email(email)
        ok = await verify_password(password, user.password_hash if user else None)
        if not user or not ok:
            raise ApiError("SESSION_INVALID")
        if not user.is_active:
            raise ApiError("ACCOUNT_DEACTIVATED")
        return user

    async def open_session(self, user, *, user_agent: str | None, ip: str | None) -> str:
        s = await self.sessions.create_session(
            user_id=user.id, expires_at=datetime.now(UTC) + ABSOLUTE_LIFETIME,
            user_agent=user_agent, ip=ip)
        return mint_token(user_id=user.id, session_id=s.id, lifetime=ABSOLUTE_LIFETIME)

    async def close_session(self, session_id: int) -> None:
        await self.sessions.revoke(session_id, datetime.now(UTC))

    # ── the request identity ───────────────────────────────────────────────
    async def principal_for(self, claims: TokenClaims) -> Principal:
        """Verified claims -> a principal, or a refusal.

        Runs AFTER `set_config('app.user_id', …)`, which is what makes the
        session row readable at all — `sessions` is under FORCE ROW LEVEL
        SECURITY (`SW-ADR-136 B`).

        **`sub` selects the scope; the session row grants the access.** A forged
        `sub` scopes the attacker to their own rows, so the `jti` is not found
        there and this fails closed.
        """
        session = await self.sessions.get_session(claims.jti)
        if session is None or session.user_id != claims.sub:
            raise ApiError("SESSION_INVALID")

        now = datetime.now(UTC)
        if session.revoked_at is not None or session.expires_at <= now:
            raise ApiError("SESSION_INVALID")

        user = await self.users.by_id(claims.sub)
        if user is None:
            raise ApiError("SESSION_INVALID")
        if not user.is_active:
            # Re-read every request, so deactivating someone takes effect on
            # their next request rather than in thirty days.
            raise ApiError("ACCOUNT_DEACTIVATED")

        if session.last_seen_at + _idle_window(user.role) <= now:
            raise ApiError("SESSION_INVALID")

        # Throttled to once a minute, decided in Python from the row already
        # fetched — no extra read, and no write on most requests (`SW-ADR-022`).
        if session.last_seen_at + timedelta(minutes=1) <= now:
            await self.sessions.touch(session.id, now)

        return self._principal(user)


def read_claims(token: str) -> TokenClaims:
    try:
        return read_token(token)
    except TokenError as exc:
        raise ApiError("SESSION_INVALID") from exc
