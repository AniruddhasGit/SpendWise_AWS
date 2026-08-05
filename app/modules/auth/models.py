"""`sessions` and `password_resets` — owned by the auth module (`SW-ADR-132`).

`sessions` is under row-level security. `password_resets` is **outside** it
(`SW-ADR-071`): redeeming a code is unauthenticated by definition, so a policy
keyed on the request identity could never serve the lookup.

The `sessions` policy is also what makes ordering load-bearing at request time —
`set_config('app.user_id', …)` must run **before** the session lookup, or the
lookup returns zero rows for every request ever made (`SW-ADR-136`).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Text, func,
)
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Nullable, which is what makes the partial index below possible (SW-ADR-076).
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "user_agent IS NULL OR char_length(user_agent) <= 500", name="user_agent"),
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_last_seen_at", "last_seen_at"),
        # PARTIAL: live sessions only. Every request checks revocation, revoked
        # rows accumulate forever, and indexing them would grow the index without
        # ever serving a lookup (`SW-ADR-039`).
        Index("ix_sessions_revoked_at__where_revoked_at_is_null", "revoked_at",
              postgresql_where=revoked_at.is_(None)),
    )


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # The HASH, never the token. The raw code is shown once and never stored —
    # a database dump must not be a set of working password resets (`SW-ADR-032`).
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        # SHA-256 hex is exactly 64 characters. Anything shorter means something
        # other than a hash got stored — which is the failure worth catching.
        CheckConstraint("char_length(token_hash) = 64", name="token_hash"),
        Index("uq_password_resets_token_hash", "token_hash", unique=True),
        Index("ix_password_resets_user_id__expires_at", "user_id", "expires_at"),
    )
