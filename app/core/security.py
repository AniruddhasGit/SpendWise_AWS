"""Password hashing and session tokens.

The token carries a **closed** claim set — `sub`, `jti`, `iat`, `exp`
(`SW-ADR-136 A`). `sub` is the `users.id` that `set_config('app.user_id', …)`
is seeded from, as the first statement of the request transaction. An unlisted
claim is ignored, never trusted.

**`sub` selects a scope; the session row grants the access.** A forged `sub`
scopes the attacker to their own rows, so the `jti` will not be found there and
the request fails closed. That separation is what lets the identity be read from
the token before the database has confirmed anything.

Three things here are one-line mistakes with large consequences:

* **`algorithms=["HS256"]` is pinned on decode.** Omit it and PyJWT will honour
  the token's own `alg` header — `alg: none` is then a valid signature
  (`SW-ADR-080`, and the `>=2.4` floor in `pyproject.toml` is for the same CVE).
* **bcrypt runs off the event loop.** Cost 12 is ~250ms of pure CPU; awaiting it
  inline stalls every other request on the worker.
* **The password check runs even for an unknown email.** Returning early makes
  "no such account" measurably faster than "wrong password", which is an account
  enumeration oracle timed with a stopwatch (`SRC-001 §10.5`).
"""
from __future__ import annotations

import asyncio
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.settings import get_settings

ALGORITHM = "HS256"
BCRYPT_ROUNDS = 12                 # SRC-001 §10.5
BCRYPT_MAX_BYTES = 72              # bcrypt truncates beyond this, silently

# A pre-computed hash of a value nobody will ever present. Verified against when
# the email is unknown, so the timing of the two paths matches.
_DUMMY_HASH = bcrypt.hashpw(b"spendwise-timing-equaliser", bcrypt.gensalt(BCRYPT_ROUNDS))


def _hash_sync(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:BCRYPT_MAX_BYTES],
                         bcrypt.gensalt(BCRYPT_ROUNDS)).decode()


def _verify_sync(password: str, hashed: str | None) -> bool:
    """Constant-ish work whether or not the account exists.

    When `hashed` is None the comparison still runs, against a dummy — so an
    unknown email costs the same ~250ms as a wrong password.
    """
    candidate = password.encode()[:BCRYPT_MAX_BYTES]
    if hashed is None:
        bcrypt.checkpw(candidate, _DUMMY_HASH)
        return False
    return bcrypt.checkpw(candidate, hashed.encode())


async def hash_password(password: str) -> str:
    """Off the event loop. Cost 12 is deliberate CPU, and awaiting it inline
    would block every concurrent request on this worker for a quarter second."""
    return await asyncio.to_thread(_hash_sync, password)


async def verify_password(password: str, hashed: str | None) -> bool:
    return await asyncio.to_thread(_verify_sync, password, hashed)


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """The closed claim set. Anything else in the token is ignored."""

    sub: int
    jti: int
    iat: datetime
    exp: datetime


class TokenError(Exception):
    """Every failure mode collapses to one exception, on purpose.

    Expired, revoked-secret, malformed, `alg: none`, missing claim — the caller
    returns `SESSION_INVALID` with one sentence for all of them. Distinguishing
    them in the response tells an attacker which wall they hit.
    """


def mint_token(*, user_id: int, session_id: int, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),      # RFC 7519 says `sub` is a string
            "jti": str(session_id),
            "iat": now,
            "exp": now + lifetime,
        },
        get_settings().JWT_SECRET.get_secret_value(),
        algorithm=ALGORITHM,
    )


def read_token(token: str) -> TokenClaims:
    """Verify and return the claims, or raise `TokenError`.

    `algorithms=[ALGORITHM]` is the whole security of this function. Without it
    a token may nominate its own algorithm, and `none` verifies against nothing.
    """
    try:
        raw = jwt.decode(
            token,
            get_settings().JWT_SECRET.get_secret_value(),
            algorithms=[ALGORITHM],
            options={"require": ["sub", "jti", "iat", "exp"]},
        )
        return TokenClaims(
            sub=int(raw["sub"]),
            jti=int(raw["jti"]),
            iat=datetime.fromtimestamp(raw["iat"], UTC),
            exp=datetime.fromtimestamp(raw["exp"], UTC),
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise TokenError(str(exc)) from exc


def secret_fingerprint() -> str:
    """SHA-256 of the signing secret, stored in `app_meta`.

    Compared at boot: if it changed, every live session is revoked in the same
    transaction (`SW-ADR-125`). Rotating the secret already invalidates the
    signatures — this makes the *rows* agree, so the session list does not show
    sessions that can never be presented again.
    """
    return hashlib.sha256(
        get_settings().JWT_SECRET.get_secret_value().encode()).hexdigest()


def new_reset_token() -> tuple[str, str]:
    """-> `(raw, sha256_hex)`. The raw code is shown **once** and never stored.

    32 bytes from `secrets`, not `random` — the latter is seeded predictably and
    is not for anything an attacker would want to guess. Only the hash is
    persisted, so a database dump is not a set of working password resets
    (`SW-ADR-032`).
    """
    raw = secrets.token_urlsafe(32)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def new_request_id() -> str:
    return uuid.uuid4().hex
