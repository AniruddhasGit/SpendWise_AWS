"""`admin.models` — account administration; never reads an amount.

Owns **`admin_audit_log`**.

Two properties of this table are the whole of `SW-ADR-083`:

* **No foreign keys.** Deliberate. The audit log outlives its subjects — a row
  about a person must survive the person, or the record is only as durable as
  the thing it is a record of.
* **Immutable at the database.** `UPDATE` and `DELETE` are revoked from the
  runtime role *and* a trigger raises. Two mechanisms, because a revoked
  privilege fails with a permission error that reads like misconfiguration,
  while the trigger's message says what the rule is.

The `action` column carries a **CHECK against a nine-item allowlist**. An
action the schema does not know is refused by PostgreSQL, so a new admin
capability cannot be added without a migration that says so out loud.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base

# The nine of `SW-ADR-105`, mirrored from the CHECK constraint so the service
# can refuse an unlisted action *before* the write rather than catching an
# IntegrityError afterwards — the difference between a refusal that names the
# problem and a 500 that does not. `test_models_match_the_spec` asserts this
# tuple against the constraint, so the mirror cannot drift.
ACTIONS = (
    "password_reset_issued",
    "sessions_revoked",
    "user_deactivated",
    "user_reactivated",
    "role_changed",
    "bootstrap_admin_claimed",
    "users_list_viewed",
    "sessions_list_viewed",
    "audit_log_viewed",
)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "action IN (" + ", ".join(f"'{a}'" for a in ACTIONS) + ")", name="action"),
    )
