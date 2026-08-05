"""`expenses` — the money table. Owned by the expenses module (`SW-ADR-132`).

The only table where a mistake costs someone their record of what they spent,
and the only one whose isolation is enforced **twice**: every query filters on
the verified identity, and PostgreSQL row-level security enforces it again with
`FORCE ROW LEVEL SECURITY` on.

Three column decisions that are load-bearing rather than stylistic:

* **`amount_paise` is BIGINT, never numeric and never a float.** Integer minor
  units throughout (`CONSTITUTION` Art V.1). The upper bound is a `CHECK`
  because the overflow risk is the **cast** of `SUM()` back to a bounded
  integer, not the sum itself (`SW-ADR-079`).
* **`category_id` is nullable**, and the composite FK is `ON DELETE NO ACTION` —
  not `SET NULL`, which would try to null `user_id` too and fail against
  `NOT NULL`. The service nulls `category_id` explicitly inside the delete
  transaction (`SW-ADR-072`).
* **`spent_on` is a plain DATE.** The day the person says they spent, not the
  instant they typed it — and never defaulted server-side (`SW-ADR-111`).
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, Date, DateTime, ForeignKey,
    ForeignKeyConstraint, Identity, Index, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base

# SW-ADR-079. 10^12 paise is ten billion rupees — far above any personal
# expense, and low enough that a bigint SUM cannot overflow before the CHECK
# would have refused the row.
MAX_AMOUNT_PAISE = 1_000_000_000_000


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False, server_default="INR")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    spent_on: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())
    # NULL until first update — a fact worth keeping. A trigger would make
    # "never edited" unrepresentable (CV-09).
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "amount_paise > 0 AND amount_paise <= 1000000000000", name="amount_paise"),
        CheckConstraint("currency = 'INR'", name="currency"),
        CheckConstraint(
            "description IS NULL OR char_length(description) <= 500", name="description"),
        # A STATIC sanity bound. The tight window — today −10y … +1y — lives in
        # the Pydantic layer, because a CHECK cannot reference now() (SW-ADR-111).
        # Two layers at two granularities, deliberately, not a contradiction.
        CheckConstraint(
            "spent_on BETWEEN DATE '2000-01-01' AND DATE '2100-12-31'", name="spent_on"),
        CheckConstraint(
            "receipt_key IS NULL OR char_length(receipt_key) <= 512", name="receipt_key"),
        # THE COMPOSITE FOREIGN KEY (SW-ADR-072). This is what makes a
        # cross-person read achieved through a WRITE impossible: person B cannot
        # point an expense at person A's category, because (category_id, user_id)
        # must exist TOGETHER in `categories`. Enforced by the database, not by a
        # pre-read the application could forget.
        ForeignKeyConstraint(
            ["category_id", "user_id"],
            ["categories.id", "categories.user_id"],
            ondelete="NO ACTION",
            name="category_id_user_id",
        ),
        Index("ix_expenses_user_id__spent_on_desc", "user_id", spent_on.desc()),
        Index("ix_expenses_user_id__category_id", "user_id", "category_id"),
    )
