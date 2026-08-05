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
                         role: str | None, active: bool | None,
                         deleted: bool | None) -> tuple[list[User], int]:
        """The account list. **`deleted=None` includes closed accounts.**

        That default is `CR-001 §2`'s and it is the opposite of the instinct: an
        administrator looking for someone who has left must be able to find them,
        and a list that silently hides them turns "restore this account" into a
        support ticket about a person who appears never to have existed.

        Which is also why the deleted predicate lives HERE and never in
        `UserRepository.by_email`/`by_id`. Filtering closed rows out at the
        repository would make deletion look like a clean win — until the admin
        console, the audit log's `target_user_id` and the last-admin guard all
        started disagreeing about who exists. The rows stay visible to queries;
        the SERVICE decides who may sign in.
        """
        where = self._search(q)
        if role:
            where.append(User.role == role)
        if active is not None:
            where.append(User.is_active.is_(active))
        if deleted is not None:
            # `is_(None)` / `is_not(None)`, never `== None`: SQL's NULL does not
            # compare equal to itself, so `deleted_at = NULL` matches no row at
            # all and `deleted=false` would return an empty list rather than
            # every live account.
            where.append(User.deleted_at.is_(None) if not deleted
                         else User.deleted_at.is_not(None))

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

    async def daily_for(self, user_id: int, from_: date, to: date) -> list[tuple]:
        """`(day, total_paise, entries)` per day — **and nothing else, ever**.

        `CR-001`, `SW-ADR-151`. The sibling of `stats_for`, built the same way and
        for the same reason: `admin_user_daily()` is `SECURITY DEFINER`, runs as
        the table owner, and swaps `app.user_id` to the target and back. Without
        the swap it would return nothing for every account but the caller's —
        silently, as an empty series that reads as "this person spends nothing"
        rather than as an error (`SW-ADR-149`).

        `CR-001` moved `SRC-001 §4.2`'s line so that `total_paise` may now be
        read; it did not move the rest. The function's `RETURNS TABLE` clause
        declares **three columns and no fourth** — no `category_id`, no
        `description`, no expense id — so "which categories" stays unanswerable
        at the DATABASE and not merely absent from a response model. Widening
        this query is not possible without a migration, deliberately.

        Only days with rows come back; the zero days are filled in the service,
        by the same code path as the person's own summary.
        """
        rows = await self.db.execute(
            text("SELECT day, total_paise, entries FROM admin_user_daily(:u, :f, :t)"),
            {"u": user_id, "f": from_, "t": to})
        # Cast at the boundary. The function declares BIGINT, but a `SUM()` over
        # one is `numeric` in PostgreSQL and arrives as a `Decimal` the moment
        # anybody edits the body — and a `Decimal` that reaches a response model
        # is CONSTITUTION Art V.2. Cheap here, unfindable later.
        return [(r[0], int(r[1] or 0), int(r[2] or 0)) for r in rows]

    async def set_active(self, user_id: int, is_active: bool) -> int:
        """Reactivating also CLEARS `deleted_at` (`CR-001 §2`).

        Restoring an account is ONE action, not two. The alternative — an admin
        who reactivates a closed account and finds sign-in still refused, because
        `principal_for` checks `deleted_at` independently — is a half-restored
        account with no control anywhere in the product to finish the job.

        Deactivating does the reverse of nothing: it must NOT set `deleted_at`.
        Pausing an account is not closing it, and collapsing the two would make
        `POST /api/auth/deactivate` and `DELETE /api/auth/me` indistinguishable
        the moment an administrator touched either.
        """
        values: dict = {"is_active": is_active}
        if is_active:
            values["deleted_at"] = None
        r = await self.db.execute(
            update(User).where(User.id == user_id).values(**values))
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
        deleted = await self.db.scalar(
            select(func.count()).select_from(User)
            .where(User.deleted_at.is_not(None))) or 0
        # THREE numbers that sum to the total, not two that overlap.
        #
        # `deactivated` was `total - active`, which was exact until CR-001 —
        # closing an account sets `is_active = false` too, so from that day a
        # closed account was reported as a paused one and the dashboard had no
        # way to say how many people had actually left. Paused now means
        # **paused and not closed**, and the arithmetic is stated here rather
        # than left to a reader to derive from two figures that quietly
        # double-count (`CR-001 §5.2`).
        return {"total": int(total), "active": int(active),
                "deleted": int(deleted),
                "deactivated": int(total) - int(active) - int(deleted),
                "admins": int(admins)}

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
