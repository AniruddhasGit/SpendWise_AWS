"""`users` — the person record. Owned by the users module (`SW-ADR-132`).

**Outside row-level security** (`SW-ADR-097`): login must read a row by email
*before* any verified identity exists, so a policy keyed on the request GUC
could never serve it. Four compensating controls are recorded there; this is a
waiver the client holds open (`OPEN-USERSRLS-01`).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Identity, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    # Two values on a column, not a table (SRC-001 §4.1). A roles table for two
    # values is a join on every request to learn something a CHECK already knows.
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default="user")
    currency: Mapped[str] = mapped_column(Text, nullable=False, server_default="INR")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("char_length(email) <= 254", name="email"),
        CheckConstraint("char_length(display_name) BETWEEN 1 AND 100", name="display_name"),
        CheckConstraint("role IN ('user','admin')", name="role"),
        CheckConstraint("currency = 'INR'", name="currency"),
        # Case-insensitive identity (SW-ADR-027). Uniqueness on lower(email), not
        # on email — otherwise Ani@x.com and ani@x.com are two accounts and the
        # second person cannot sign in.
        Index("uq_users_lower_email", func.lower(email), unique=True),
    )
