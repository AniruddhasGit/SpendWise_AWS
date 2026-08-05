"""`admin.repository` — account administration; never reads an amount.

Queries only. Never knows what HTTP is.

**This file is where the privacy guarantee is physically enforced**, so read the
`stats_for` docstring before adding a query here: the only route from an admin
to another person's expenses is a `SECURITY DEFINER` function returning two
columns, neither of which can hold money.
"""
from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import ACTIONS, AdminAuditLog
from app.modules.auth.models import Session
from app.modules.users.models import User


class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── people ─────────────────────────────────────────────────────────────
    def _search(self, q: str | None) -> list:
        if not q:
            return []
        like = f"%{q.strip().lower()}%"
        # Email AND display name, both lowered. `lower() LIKE lower()` rather
        # than ILIKE, so "found by search" and "already taken" agree about what
        # counts as the same name — the unique index is on `lower(email)`.
        return [or_(func.lower(User.email).like(like),
                    func.lower(User.display_name).like(like))]

    async def list_users(self, *, limit: int, offset: int, q: str | None,
                         role: str | None, active: bool | None
                         ) -> tuple[list[User], int]:
        where = self._search(q)
        if role:
            where.append(User.role == role)
        if active is not None:
            where.append(User.is_active.is_(active))

        total = await self.db.scalar(
            select(func.count()).select_from(User).where(*where)) or 0
        rows = await self.db.scalars(
            select(User).where(*where).order_by(User.id).limit(limit).offset(offset))
        return list(rows), int(total)

    async def stats_for(self, user_id: int) -> tuple[int, date | None]:
        """`(expense_count, last_activity)` — and **nothing else, ever**.

        `SW-ADR-129`. Calls `admin_expense_stats(BIGINT)`, a `SECURITY DEFINER`
        function that runs as the table owner and therefore sees past row-level
        security. Its `RETURNS TABLE` clause declares exactly two columns, so
        the bypass is bounded by the function signature rather than by the
        discipline of whoever writes the next query.

        The first version of this capability was a POLICY — and a policy that
        lets an admin count rows lets them `SELECT` every column of those rows.
        `SRC-001 §4.2` says an admin may not see anyone else's amounts (the
        bold **no** is the client's own), so counting had to be separated from
        reading, and only a function can do that.
        """
        row = (await self.db.execute(
            text("SELECT expense_count, last_activity FROM admin_expense_stats(:u)"),
            {"u": user_id})).one()
        return int(row[0] or 0), row[1]

    async def set_active(self, user_id: int, is_active: bool) -> int:
        r = await self.db.execute(
            update(User).where(User.id == user_id).values(is_active=is_active))
        return r.rowcount or 0

    async def set_role(self, user_id: int, role: str) -> int:
        r = await self.db.execute(
            update(User).where(User.id == user_id).values(role=role))
        return r.rowcount or 0

    async def count_active_admins(self, *, excluding: int | None = None) -> int:
        """**Active** administrators, not merely `role='admin'`.

        A deactivated admin cannot sign in, so counting them would let the last
        usable administrator be demoted while the guard reported two — which is
        the state `SRC-001 §4.4` exists to make unreachable.
        """
        where = [User.role == "admin", User.is_active.is_(True)]
        if excluding is not None:
            where.append(User.id != excluding)
        return await self.db.scalar(
            select(func.count()).select_from(User).where(*where)) or 0

    # ── sessions ───────────────────────────────────────────────────────────
    async def sessions_for(self, user_id: int) -> list:
        """One person's LIVE sessions, most recently seen first.

        Through `admin_user_sessions()`, not a query, for the reason the whole
        admin module keeps running into: `sessions` carries **exactly one
        policy**, keyed on `app.user_id`, so an admin selecting from it sees
        only their own rows. `SRC-001 §4.2` grants "see who is currently signed
        in" to an admin and the table made it unreachable — silently, returning
        an empty list that reads as "nobody is signed in".

        The function's RETURN TYPE declares no `ip` and no `user_agent`, which
        makes `SW-ADR-106` structurally true at the DATABASE and not only in a
        Pydantic model.
        """
        rows = await self.db.execute(
            text("SELECT id, user_id, issued_at, last_seen_at, expires_at, "
                 "revoked_at FROM admin_user_sessions(:u)"), {"u": user_id})
        return list(rows)

    async def revoke_sessions(self, user_id: int) -> int:
        """Through `admin_revoke_sessions()`.

        A plain `UPDATE sessions WHERE user_id = :other` matches **zero rows
        under RLS and reports success** — a force-sign-out that signs nobody
        out, plus an audit row claiming it did. The same silent shape
        `FORCE ROW LEVEL SECURITY` produced for the owner in `SW-ADR-081`.
        """
        return int((await self.db.execute(
            text("SELECT revoked FROM admin_revoke_sessions(:u)"),
            {"u": user_id})).scalar_one())

    # ── the audit log ──────────────────────────────────────────────────────
    async def write_audit(self, *, admin_id: int, action: str,
                          target_user_id: int | None = None,
                          details: dict | None = None) -> AdminAuditLog:
        """One row, in the CALLER'S transaction.

        Never its own session, never a savepoint: `SRC-001 §10.8` says the
        audit row and the change it records commit together or neither does,
        and a savepoint here would let the change roll back while the claim
        that it happened survived.
        """
        if action not in ACTIONS:
            # Refused BEFORE the write. The CHECK constraint would catch it
            # too — as an IntegrityError that aborts the transaction, so the
            # audit row's failure would take the change with it and a typo
            # would surface as a 500.
            raise ValueError(
                f"{action!r} is not one of the nine audited actions. The list in "
                f"admin_audit_log's CHECK constraint is CLOSED: adding a capability "
                f"means a migration, not a new string.")
        row = AdminAuditLog(admin_id=admin_id, action=action,
                            target_user_id=target_user_id, details=details or {})
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_audit(self, *, limit: int, offset: int, action: str | None,
                         target_user_id: int | None) -> tuple[list[AdminAuditLog], int]:
        where = []
        if action:
            where.append(AdminAuditLog.action == action)
        if target_user_id is not None:
            where.append(AdminAuditLog.target_user_id == target_user_id)
        total = await self.db.scalar(
            select(func.count()).select_from(AdminAuditLog).where(*where)) or 0
        rows = await self.db.scalars(
            select(AdminAuditLog).where(*where)
            .order_by(AdminAuditLog.id.desc())
            .limit(limit).offset(offset))
        return list(rows), int(total)

    # ── the overview ───────────────────────────────────────────────────────
    async def account_counts(self) -> dict:
        """Totals for the admin dashboard. Counts of ACCOUNTS, never of money."""
        total = await self.db.scalar(select(func.count()).select_from(User)) or 0
        active = await self.db.scalar(
            select(func.count()).select_from(User).where(User.is_active.is_(True))) or 0
        admins = await self.db.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")) or 0
        return {"total": int(total), "active": int(active),
                "deactivated": int(total) - int(active), "admins": int(admins)}

    async def signups_by_day(self, since: date) -> list[tuple[date, int]]:
        """New accounts per day — the one time series an admin can honestly
        plot, because it is derived from `users.created_at` and not from
        anybody's spending.

        Grouped in **Asia/Kolkata** (`SW-ADR-096`), not UTC: a signup at 02:00
        IST is the same calendar day as one at 23:00 IST, and grouping in UTC
        would split them.
        """
        day = func.date(func.timezone("Asia/Kolkata", User.created_at)).label("d")
        rows = await self.db.execute(
            select(day, func.count().label("n"))
            .where(func.date(func.timezone("Asia/Kolkata", User.created_at)) >= since)
            .group_by(day).order_by(day))
        return [(r.d, int(r.n)) for r in rows]
