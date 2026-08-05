"""`categories` — owned by the categories module. Protected by RLS."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, Index, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("char_length(name) BETWEEN 1 AND 50", name="name"),
        CheckConstraint("color ~ '^#[0-9a-f]{6}$'", name="color"),
        # The target of the composite FK from expenses (SW-ADR-072). Without
        # this unique index the composite reference cannot exist.
        Index("uq_categories_id__user_id", "id", "user_id", unique=True),
        # Unique per person, case-insensitively (SW-ADR-033).
        Index("uq_categories_user_id__lower_name", "user_id", func.lower(name), unique=True),
        Index("ix_categories_user_id", "user_id"),
    )
