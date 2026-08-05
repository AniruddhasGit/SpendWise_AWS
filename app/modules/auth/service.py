"""Registration, sign-in, sign-out, and turning a token into a principal.

The layer that translates. It calls the users and categories **services** — the
sanctioned kind of crossing — and never touches their tables directly.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import set_request_identity
from app.core.errors import ApiError, Violation, validation_error
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
        if not user or not ok or not user.is_active or user.deleted_at is not None:
            # ONE refusal for all four. `SW-ADR-100 (1)`: "Login refused with
            # the same generic 401 as any bad credential, bcrypt compare still
            # run." A distinct code for a deactivated account tells anyone who
            # can type an address that it exists and has been disabled.
            #
            # A DELETED account is folded into the same condition rather than
            # given a branch of its own, and that is the whole reason `CR-001`
            # could add soft deletion without touching the error registry. The
            # temptation is `ACCOUNT_DELETED` — which would be an enumeration
            # oracle with a friendlier name: a soft-deleted account keeps its
            # email address (the unique index on `lower(email)` stays total), so
            # anyone typing an address would learn both that the person existed
            # AND that they have left. Same 401, same sentence, same timing.
            #
            # `ACCOUNT_DEACTIVATED` is for a VALID SESSION whose account was
            # switched off underneath it (`error_codes`: "valid session,
            # is_active false") — the person is already identified there, so
            # there is nothing left to disclose and everything to explain.
            raise ApiError("SESSION_INVALID")
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
        if not user.is_active or user.deleted_at is not None:
            # Re-read every request, so deactivating someone takes effect on
            # their next request rather than in thirty days.
            #
            # `deleted_at` is checked SEPARATELY even though `delete_self` sets
            # `is_active = False` in the same transaction, because the two
            # columns are two facts and only one of them is being relied on
            # here. Deriving "closed" from "paused" would make the refusal
            # depend on a write in another method staying correct forever; a
            # future path that reactivates without clearing `deleted_at` would
            # then hand a deleted account a working session, silently.
            #
            # `ACCOUNT_DEACTIVATED` for both, and deliberately: the person is
            # already identified by a valid session, so there is nothing left to
            # disclose — and the client renders one "your account is closed"
            # screen either way (`CR-001 §2`).
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


def validate_password(password: str) -> None:
    """12-72 bytes (`SW-ADR-103`), checked HERE as well as in the request model.

    The upper bound is bcrypt's: it silently ignores bytes past 72, so without
    the cap two different long passwords sharing a 72-byte prefix are the same
    password and nobody is told. The reset and change-password paths do not go
    through `RegisterRequest`, so the rule has to live somewhere both can call
    — and one function is what stops the two from drifting.
    """
    if not 12 <= len(password.encode("utf-8")) <= 72:
        raise validation_error([Violation("field.type", "password")])


# ── M1/M4: reset codes, and the settings a person owns ─────────────────────
RESET_LIFETIME = timedelta(hours=1)


class AccountService(AuthService):
    """The half of auth a person exercises on themselves.

    A subclass rather than a sibling because it needs the same repositories and
    the same `_principal`, and a second class holding a second copy of those is
    how two definitions of "who is this" come to exist.
    """

    async def issue_reset(self, user_id: int, *, created_by_admin_id: int) -> tuple[str, datetime]:
        """`P-ACC-07`. Returns the RAW token exactly once.

        Only the SHA-256 hash is stored (`SW-ADR-032`), so a database dump is
        not a set of working password resets — and this return value is the
        only moment the code exists in the clear anywhere in the system. It is
        never logged: `SW-ADR-138`'s deny-list covers `token`.
        """
        from app.core.security import new_reset_token
        from app.modules.auth.models import PasswordReset

        raw, hashed = new_reset_token()
        expires_at = datetime.now(UTC) + RESET_LIFETIME
        self.db.add(PasswordReset(
            user_id=user_id, token_hash=hashed, expires_at=expires_at,
            created_by_admin_id=created_by_admin_id))
        await self.db.flush()
        return raw, expires_at

    async def redeem_reset(self, *, token: str, new_password: str) -> None:
        """`P-ACC-07`, all four outcomes with ONE message.

        Unknown, expired, already used and valid-but-weak-password are four
        different states, and three of them return the same sentence — telling
        an attacker which one they hit turns a guessed token into an oracle.
        The fourth (a weak password) is the caller's own input and is named.
        """
        from sqlalchemy import select

        from app.core.security import hash_reset_token
        from app.modules.auth.models import PasswordReset

        validate_password(new_password)

        now = datetime.now(UTC)
        row = await self.db.scalar(
            select(PasswordReset).where(
                PasswordReset.token_hash == hash_reset_token(token)))
        if row is None or row.used_at is not None or row.expires_at <= now:
            raise ApiError("SESSION_INVALID")

        user = await self.users.by_id(row.user_id)
        if user is None:
            raise ApiError("SESSION_INVALID")

        # ESTABLISH THE IDENTITY before touching `sessions`.
        #
        # This route is unauthenticated by design — the point of a reset is that
        # the person cannot sign in — so no dependency has set `app.user_id`,
        # and `sessions` is under FORCE ROW LEVEL SECURITY. The revocation below
        # would match zero rows, leaving every session of a possibly-compromised
        # account live while the response said the reset succeeded.
        #
        # Setting it here is not a weakening: possession of the token IS the
        # proof of identity this endpoint accepts, and it has just been checked.
        await set_request_identity(self.db, row.user_id)

        user.password_hash = await hash_password(new_password)
        row.used_at = now
        # Redeeming ends every session. A reset exists because the account may
        # be compromised; leaving the attacker's session live would make the
        # reset a formality.
        await self.sessions.revoke_all_for_user(row.user_id, now)
        await self.db.flush()

    async def update_profile(self, principal: Principal, *, display_name: str | None):
        user = await self.users.by_id(principal.id)
        if user is None:                                    # pragma: no cover
            raise ApiError("SESSION_INVALID")
        if display_name is not None:
            name = display_name.strip()
            if not 1 <= len(name) <= 100:
                raise validation_error([Violation("field.type", "display_name")])
            user.display_name = name
        await self.db.flush()
        return self._principal(user)

    async def change_password(self, principal: Principal, *, current: str,
                              new: str, keep_session_id: int) -> int:
        """Changing a password signs out EVERY OTHER session, not this one.

        Signing the person out of the browser they are standing in punishes the
        action this feature exists to encourage. Every other session goes,
        because "change my password" is what someone does when they think
        another session is not theirs.
        """
        validate_password(new)
        user = await self.users.by_id(principal.id)
        if user is None or not await verify_password(current, user.password_hash):
            # The SAME code a bad sign-in returns. A distinct one would confirm
            # a guessed password against a session someone already stole.
            raise ApiError("SESSION_INVALID")

        user.password_hash = await hash_password(new)
        await self.db.flush()
        return await self.sessions.revoke_all_except(principal.id, keep_session_id,
                                                     datetime.now(UTC))

    async def deactivate_self(self, principal: Principal) -> None:
        """`SW-ADR-148`. Deactivation, not deletion.

        `SW-ADR-107` ruled that user deletion did not exist in v1 — and has
        since been superseded by `SW-ADR-150`, so it does. Deactivation did not
        become redundant when it arrived: **pause me** and **close it** are
        different requests, and `delete_self` below is the other one.

        This is the pause: sign-in refused, every session revoked, the record
        intact, `deleted_at` untouched, restorable by an administrator.

        The last active administrator cannot do this to themselves, for the same
        reason they cannot demote themselves: it leaves a system nobody can
        administer.
        """
        from app.modules.admin.repository import AdminRepository

        user = await self.users.by_id(principal.id)
        if user is None:                                    # pragma: no cover
            raise ApiError("SESSION_INVALID")
        if user.role == "admin":
            if await AdminRepository(self.db).count_active_admins(
                    excluding=user.id) == 0:
                raise ApiError("CONFLICT", field="is_active")

        user.is_active = False
        await self.sessions.revoke_all_for_user(user.id, datetime.now(UTC))
        await self.db.flush()

    async def delete_self(self, principal: Principal) -> None:
        """`CR-001`, `SW-ADR-150`. Soft deletion — the account closes, the rows stay.

        `POST /api/auth/deactivate` is "pause me"; this is "close it". They stay
        two endpoints because they are two intentions, and a person who asks to
        delete their account and gets a deactivation has been told something
        untrue about what just happened. Both are reversible by an administrator;
        only one of them says so on the tin.

        **What is NOT deleted: everything.** Every expense, every category, every
        audit row, and the person record itself survive untouched.

        `SW-ADR-107`, superseded by `SW-ADR-150`, called hard deletion the
        clearest one-way door in the register. The client asked for the soft
        form by name, and that is the version which does not walk through it.

        The last active administrator cannot do this — same guard, same code and
        same field as `deactivate_self`, because it is the same failure: a system
        nobody can administer. It runs FIRST, before any column is touched, so a
        refused delete leaves the row exactly as it found it.

        `deleted_at` AND `is_active = False` together, in one transaction with
        the revocations. Setting only `deleted_at` would leave every
        `is_active`-shaped guard in this system — `count_active_admins`, the
        admin overview's counts, `set_active`'s last-admin check — reading a
        closed account as a live one.
        """
        from app.modules.admin.repository import AdminRepository

        user = await self.users.by_id(principal.id)
        if user is None:                                    # pragma: no cover
            raise ApiError("SESSION_INVALID")
        if user.role == "admin":
            if await AdminRepository(self.db).count_active_admins(
                    excluding=user.id) == 0:
                raise ApiError("CONFLICT", field="is_active")

        now = datetime.now(UTC)
        user.deleted_at = now
        user.is_active = False
        # Revoked in the SAME transaction, not left to expire. `principal_for`
        # refuses a deleted account on the next request anyway, but that is a
        # check and this is the row — and `E4-S3` is the rule that the two agree
        # rather than one covering for the other. Every device the person is
        # signed in on is signed out by this call, including the one that made it
        # (the handler then clears the cookie).
        await self.sessions.revoke_all_for_user(user.id, now)
        await self.db.flush()
