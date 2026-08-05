"""Wire shapes for auth. From `contract.json` -> `request_models`."""
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(extra="ignore", strict=True)

# A SHAPE check, not `EmailStr`.
#
# `EmailStr` rejects `a@spendwise.test` because `.test` is an IANA special-use
# TLD - and that is the exact address `contract.json`'s seed fixture mandates
# and `BOOTSTRAP_ADMIN_EMAIL` uses. Reserved TLDs are the correct choice for a
# fixture precisely because they can never be real, so a validator that refuses
# them is refusing the right answer.
#
# Deliverability validation would also be theatre here: `SW-ADR-012` records
# that there is NO EMAIL IN THE STACK - which is why password reset is
# administrator-issued rather than self-service. Nothing is ever sent, so the
# only useful question is whether the value has the shape of an address, and
# the database already caps it at 254 characters.
Email = Annotated[str, Field(min_length=3, max_length=254,
                             pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class RegisterRequest(BaseModel):
    model_config = STRICT
    email: Email
    # 12-72 bytes (SW-ADR-103). The upper bound is bcrypt's: it IGNORES bytes
    # past 72, so without this cap two different long passwords sharing a
    # 72-byte prefix would both unlock the account.
    password: str = Field(min_length=12, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    model_config = STRICT
    email: Email
    password: str


class Principal(BaseModel):
    """What `GET /api/auth/me` returns, and what register/login return too.

    Carries `currency` because the expenses service reads it from HERE and never
    from the users table (`CV-05`, `SRC-001 §3.4`), and `receipts_enabled` so the
    client can hide the receipt control when storage is unconfigured rather than
    letting it fail (`P-ACC-06`).
    """
    id: int
    email: str
    display_name: str
    role: str
    currency: str
    is_active: bool
    receipts_enabled: bool


# ── the settings a person owns (SW-ADR-148) ────────────────────────────────
class ProfileUpdate(BaseModel):
    """`PATCH /api/auth/me`. Display name only.

    Email is absent deliberately: it is the identity the unique index is built
    on, changing it is an account takeover vector when nothing verifies the new
    address, and `SW-ADR-012` records that there is no email in this stack to
    verify with.
    """

    model_config = ConfigDict(extra="ignore", strict=True)
    display_name: str | None = None


class PasswordChange(BaseModel):
    """`POST /api/auth/password`. Both, always.

    Requiring the current password is what stops a stolen session becoming a
    stolen account — without it, anyone holding a live cookie can lock the
    owner out.
    """

    model_config = ConfigDict(extra="ignore", strict=True)
    current_password: str
    new_password: str


class ResetComplete(BaseModel):
    """`POST /api/auth/reset/complete`. Redeeming an admin-issued code."""

    model_config = ConfigDict(extra="ignore", strict=True)
    token: str
    new_password: str
