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
    # SOFT deletion (`CR-001`, `SW-ADR-150`). A timestamp, not a boolean: "when"
    # answers "whether" as well, and an administrator restoring an account needs
    # to know how long it was closed.
    #
    # `SW-ADR-107` ruled that user deletion does not exist in v1 because deleting
    # a person's financial history is the clearest one-way door in the register —
    # and its own text named the form deletion would arrive in when it came. This
    # is that form: every expense, category and audit row the person owns is
    # untouched, and only sign-in changes.
    #
    # It is set ALONGSIDE `is_active = false`, never instead of it. Two columns
    # because they answer two questions — "paused" and "closed" — and a single
    # tri-state column would make `POST /api/auth/deactivate` and
    # `DELETE /api/auth/me` indistinguishable at the row.
    #
    # **The unique index on `lower(email)` below stays TOTAL**, deliberately: a
    # partial index excluding deleted rows would let the same address register
    # again and create two rows sharing one identity, which every lookup in this
    # system would then have to disambiguate correctly, forever (`CR-001 §2`).
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)

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
