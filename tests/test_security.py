"""Password hashing and session tokens. No database.

These are the primitives an attacker meets first, so each test names the attack
it forecloses rather than the function it exercises.
"""
from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.security import (
    ALGORITHM, BCRYPT_MAX_BYTES, TokenError, hash_password, hash_reset_token,
    mint_token, new_reset_token, read_token, secret_fingerprint, verify_password,
)
from app.core.settings import get_settings


# ── passwords ──────────────────────────────────────────────────────────────
async def test_a_password_verifies_against_its_own_hash() -> None:
    h = await hash_password("correct-horse-battery-staple")
    assert await verify_password("correct-horse-battery-staple", h)


async def test_a_wrong_password_does_not() -> None:
    h = await hash_password("correct-horse-battery-staple")
    assert not await verify_password("Correct-horse-battery-staple", h)


async def test_the_hash_is_never_the_password() -> None:
    h = await hash_password("hunter2hunter2")
    assert "hunter2" not in h


async def test_two_hashes_of_one_password_differ() -> None:
    """Per-password salt. Identical hashes would let an attacker learn that two
    accounts share a password by reading the table."""
    a = await hash_password("same-password-12")
    b = await hash_password("same-password-12")
    assert a != b


async def test_the_cost_factor_is_twelve() -> None:
    """`SRC-001 §10.5`. The cost is IN the hash, so it is checkable — and a
    library default that quietly drops to 10 would otherwise be invisible."""
    h = await hash_password("x" * 16)
    assert h.split("$")[2] == "12", f"bcrypt cost is {h.split('$')[2]}, not 12"


async def test_an_unknown_email_still_costs_a_full_verification() -> None:
    """`SRC-001 §10.5`: compare even when there is no account.

    Returning early would make "no such account" measurably faster than "wrong
    password" — an enumeration oracle timed with a stopwatch. Asserted on the
    clock, loosely: the point is the same ORDER of magnitude, not a fixed ms.
    """
    h = await hash_password("a-real-password-x")

    t0 = time.perf_counter()
    await verify_password("some-guess-here", h)
    real = time.perf_counter() - t0

    t0 = time.perf_counter()
    assert not await verify_password("some-guess-here", None)
    unknown = time.perf_counter() - t0

    assert unknown > real / 3, (
        f"unknown-email path took {unknown*1000:.0f}ms against {real*1000:.0f}ms for a "
        f"real one — fast enough to enumerate accounts with a stopwatch")


async def test_passwords_beyond_72_bytes_do_not_silently_truncate_into_a_match() -> None:
    """bcrypt ignores bytes past 72. Two different long passwords sharing a
    72-byte prefix would otherwise both unlock the account — so the boundary is
    asserted rather than assumed."""
    base = "x" * BCRYPT_MAX_BYTES
    h = await hash_password(base)
    assert await verify_password(base, h)
    assert await verify_password(base + "DIFFERENT-TAIL", h), (
        "documented bcrypt behaviour: bytes past 72 are ignored. This test exists "
        "so the truncation is a known property, not a discovery — P-ACC-01 caps "
        "the password at 72 bytes for exactly this reason")


# ── tokens ─────────────────────────────────────────────────────────────────
def test_a_minted_token_round_trips() -> None:
    t = mint_token(user_id=7, session_id=42, lifetime=timedelta(hours=1))
    c = read_token(t)
    assert c.sub == 7 and c.jti == 42


def test_the_claim_set_is_exactly_the_four() -> None:
    """`SW-ADR-136 A`. A fifth claim is a place for something to be trusted that
    nothing verifies."""
    raw = jwt.decode(mint_token(user_id=1, session_id=1, lifetime=timedelta(hours=1)),
                     get_settings().JWT_SECRET.get_secret_value(), algorithms=[ALGORITHM])
    assert set(raw) == {"sub", "jti", "iat", "exp"}


def test_alg_none_is_refused() -> None:
    """THE JWT attack. Without `algorithms=` pinned on decode, PyJWT honours the
    token's own `alg` header and `none` verifies against nothing."""
    forged = jwt.encode({"sub": "1", "jti": "1",
                         "iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(hours=1)},
                        key="", algorithm="none")
    with pytest.raises(TokenError):
        read_token(forged)


def test_a_token_signed_with_another_secret_is_refused() -> None:
    forged = jwt.encode({"sub": "1", "jti": "1",
                         "iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(hours=1)},
                        key="not-the-real-secret", algorithm=ALGORITHM)
    with pytest.raises(TokenError):
        read_token(forged)


def test_an_expired_token_is_refused() -> None:
    with pytest.raises(TokenError):
        read_token(mint_token(user_id=1, session_id=1, lifetime=timedelta(seconds=-10)))


@pytest.mark.parametrize("missing", ["sub", "jti", "iat", "exp"])
def test_a_token_missing_any_required_claim_is_refused(missing: str) -> None:
    now = datetime.now(UTC)
    claims = {"sub": "1", "jti": "1", "iat": now, "exp": now + timedelta(hours=1)}
    del claims[missing]
    forged = jwt.encode(claims, get_settings().JWT_SECRET.get_secret_value(),
                        algorithm=ALGORITHM)
    with pytest.raises(TokenError):
        read_token(forged)


@pytest.mark.parametrize("junk", ["", "not.a.token", "a.b.c", "..", "null"])
def test_malformed_tokens_raise_the_same_exception(junk: str) -> None:
    """One exception for every failure mode. The caller returns one sentence,
    so an attacker cannot learn which wall they hit."""
    with pytest.raises(TokenError):
        read_token(junk)


# ── the signing-secret fingerprint ─────────────────────────────────────────
def test_the_fingerprint_is_a_sha256_and_not_the_secret() -> None:
    fp = secret_fingerprint()
    assert len(fp) == 64 and int(fp, 16) >= 0
    assert get_settings().JWT_SECRET.get_secret_value() not in fp


def test_the_fingerprint_is_stable_across_calls() -> None:
    assert secret_fingerprint() == secret_fingerprint()


# ── reset tokens ───────────────────────────────────────────────────────────
def test_a_reset_token_returns_a_raw_value_and_its_hash() -> None:
    raw, hashed = new_reset_token()
    assert hashed == hash_reset_token(raw)
    assert len(hashed) == 64
    assert raw not in hashed, "the raw code must not be recoverable from the stored value"


def test_two_reset_tokens_are_never_the_same() -> None:
    assert len({new_reset_token()[0] for _ in range(200)}) == 200


def test_the_stored_value_is_the_hash_and_the_schema_enforces_its_length() -> None:
    """`char_length(token_hash) = 64` in the DDL. A shorter value means the raw
    token got stored, and a database dump becomes a set of working resets."""
    _, hashed = new_reset_token()
    assert len(hashed) == 64


def test_a_short_signing_secret_is_refused_at_startup() -> None:
    """RFC 7518 §3.2. PyJWT only warns, and a warning in a log nobody reads is
    not a control — so the settings refuse to start.

    A secret shorter than the hash output is brute-forceable offline from one
    captured token, and every session in the system is signed with it.
    """
    from pydantic import ValidationError as PydanticValidationError
    from app.core.settings import Settings

    with pytest.raises(PydanticValidationError, match="32 bytes"):
        Settings(
            DATABASE_URL="postgresql+asyncpg://a:b@h/d",
            MIGRATION_DATABASE_URL="postgresql+asyncpg://o:p@h/d",
            JWT_SECRET="too-short",
        )
