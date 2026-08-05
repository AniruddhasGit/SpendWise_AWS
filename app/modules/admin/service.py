"""`admin.service` — account administration; never reads an amount.

Every method here does two things in ONE transaction: the change, and the audit
row that records it. `SRC-001 §10.8`:

> Every admin action writes to the audit log in the same transaction as the
> change. If the audit write fails, the change doesn't happen either.

That is why no method here opens a savepoint around the audit write. A
savepoint would let the change survive a failed audit, which is precisely the
state the rule forbids — and `test_a_failed_audit_write_rolls_back_the_change`
plants a failure to prove it.

**Reads are audited too** (`E4-S5`): listing accounts, listing sessions and
reading the audit log each write one row. Looking at who exists is itself an
exercise of privilege.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.modules.admin.repository import AdminRepository
from app.modules.admin.schemas import (
    AdminOverview, AdminSession, AdminSessionPage, AdminUser, AdminUserPage,
    AuditPage, AuditRow, DayCount,
)
from app.modules.auth.schemas import Principal
from app.modules.users.repository import UserRepository

# `SW-ADR-145 A`, same reasoning: the closed error registry holds no rule that
# can refuse an over-large page size, so it is clamped and echoed back rather
# than 422'd with a borrowed code.
LIMIT_MIN, LIMIT_MAX = 1, 200


def clamp(limit: int) -> int:
    return max(LIMIT_MIN, min(LIMIT_MAX, limit))


def sentence(row) -> str:
    """One audited action, as a line a person can read.

    Rendered SERVER-SIDE (`P-ADM-08`). A client assembling this would need to
    know all nine action types and would print `[object Object]` for the tenth
    — and the tenth is exactly the row an auditor most needs to read.
    """
    who = f"user #{row.target_user_id}" if row.target_user_id else "the account list"
    d = row.details or {}
    return {
        "password_reset_issued": f"issued a password reset for {who}",
        "sessions_revoked": f"signed {who} out of {d.get('revoked', 'all')} session(s)",
        "user_deactivated": f"deactivated {who}",
        "user_reactivated": f"reactivated {who}",
        "role_changed": f"changed {who}'s role from {d.get('from', '?')} to {d.get('to', '?')}",
        "bootstrap_admin_claimed": f"claimed the bootstrap administrator role ({who})",
        "users_list_viewed": "viewed the account list",
        "sessions_list_viewed": "viewed the live session list",
        "audit_log_viewed": "read the audit log",
    }.get(row.action, f"performed {row.action}")


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AdminRepository(db)
        self.users = UserRepository(db)

    async def _target(self, user_id: int):
        target = await self.users.by_id(user_id)
        if target is None:
            # `P-PRV-03`: not-found and not-visible are the same refusal. An
            # admin can see every account, so here they genuinely coincide —
            # the shape is kept identical so the two never diverge.
            raise ApiError("NOT_FOUND")
        return target

    # ── reads ──────────────────────────────────────────────────────────────
    async def list_users(self, admin: Principal, *, limit: int, offset: int,
                         q: str | None, role: str | None,
                         active: bool | None) -> AdminUserPage:
        limit = clamp(limit)
        rows, total = await self.repo.list_users(
            limit=limit, offset=offset, q=q, role=role, active=active)

        items = []
        for u in rows:
            count, last = await self.repo.stats_for(u.id)
            items.append(AdminUser(
                id=u.id, email=u.email, display_name=u.display_name, role=u.role,
                is_active=u.is_active, created_at=u.created_at,
                expense_count=count, last_activity=last))

        await self.repo.write_audit(
            admin_id=admin.id, action="users_list_viewed",
            details={"returned": len(items), "search": q or ""})
        return AdminUserPage(items=items, total=total, limit=limit, offset=offset)

    async def _live_sessions(self, user_id: int | None) -> list:
        """One person's, or everyone's — assembled PER USER.

        `admin_user_sessions()` takes a target, because the identity swap that
        makes it work is a swap to one identity. A cross-user list is therefore
        built by walking the account page, exactly as `stats_for` already does.
        Bounded by the page size, and honest: there is no query in this system
        that returns every person's sessions at once, and inventing a policy to
        create one would be a second way to read the table.
        """
        if user_id is not None:
            return await self.repo.sessions_for(user_id)
        people, _ = await self.repo.list_users(limit=LIMIT_MAX, offset=0, q=None,
                                               role=None, active=None)
        out = []
        for u in people:
            out.extend(await self.repo.sessions_for(u.id))
        out.sort(key=lambda s: (s.last_seen_at, s.id), reverse=True)
        return out

    async def list_sessions(self, admin: Principal, *, limit: int, offset: int,
                            user_id: int | None) -> AdminSessionPage:
        limit = clamp(limit)
        rows = await self._live_sessions(user_id)
        total = len(rows)
        page = rows[offset:offset + limit]
        await self.repo.write_audit(
            admin_id=admin.id, action="sessions_list_viewed",
            target_user_id=user_id, details={"returned": len(page)})
        return AdminSessionPage(
            items=[AdminSession.model_validate(s, from_attributes=True) for s in page],
            total=total, limit=limit, offset=offset)

    async def list_audit(self, admin: Principal, *, limit: int, offset: int,
                         action: str | None, target_user_id: int | None) -> AuditPage:
        limit = clamp(limit)
        rows, total = await self.repo.list_audit(
            limit=limit, offset=offset, action=action, target_user_id=target_user_id)
        items = [AuditRow(id=r.id, admin_id=r.admin_id, action=r.action,
                          target_user_id=r.target_user_id, created_at=r.created_at,
                          sentence=sentence(r)) for r in rows]
        # Reading the log is itself audited, and the row is written AFTER the
        # page is built — so a reader never sees the record of their own read
        # in the page that produced it, which would look like a bug.
        await self.repo.write_audit(
            admin_id=admin.id, action="audit_log_viewed", details={"returned": len(items)})
        return AuditPage(items=items, total=total, limit=limit, offset=offset)

    async def overview(self, admin: Principal, *, today: date) -> AdminOverview:
        """The admin dashboard.

        Reuses `users_list_viewed` for the audit row rather than inventing a
        tenth action: the CHECK constraint's list is closed, and this reads the
        account list. A new action type is a migration, deliberately.
        """
        counts = await self.repo.account_counts()
        rows, _ = await self.repo.list_users(limit=LIMIT_MAX, offset=0, q=None,
                                             role=None, active=None)

        recorded = 0
        active_7 = dormant_30 = never = 0
        for u in rows:
            n, last = await self.repo.stats_for(u.id)
            recorded += n
            if last is None:
                never += 1
            elif (today - last).days <= 7:
                active_7 += 1
            elif (today - last).days > 30:
                dormant_30 += 1

        signups = await self.repo.signups_by_day(today - timedelta(days=29))
        _, audit_total = await self.repo.list_audit(
            limit=1, offset=0, action=None, target_user_id=None)

        await self.repo.write_audit(
            admin_id=admin.id, action="users_list_viewed",
            details={"returned": len(rows), "view": "overview"})

        return AdminOverview(
            accounts_total=counts["total"], accounts_active=counts["active"],
            accounts_deactivated=counts["deactivated"], admins=counts["admins"],
            sessions_live=len(await self._live_sessions(None)),
            expenses_recorded=recorded,
            accounts_active_last_7_days=active_7,
            accounts_dormant_30_days=dormant_30,
            accounts_never_used=never,
            signups=[DayCount(date=d, count=n) for d, n in signups],
            audit_last_7_days=audit_total)

    # ── mutations ──────────────────────────────────────────────────────────
    async def revoke_sessions(self, admin: Principal, user_id: int) -> dict:
        await self._target(user_id)
        n = await self.repo.revoke_sessions(user_id)
        await self.repo.write_audit(admin_id=admin.id, action="sessions_revoked",
                                    target_user_id=user_id, details={"revoked": n})
        return {"revoked": n}

    async def set_active(self, admin: Principal, user_id: int, is_active: bool) -> dict:
        target = await self._target(user_id)

        if not is_active and target.role == "admin":
            # The last-administrator guard applies to DEACTIVATION as well as
            # demotion. Deactivating the last admin leaves a system nobody can
            # administer, and it does it without touching the role column —
            # which is why a guard that only watched roles would miss it.
            if await self.repo.count_active_admins(excluding=user_id) == 0:
                raise ApiError("CONFLICT", field="is_active",
                               message="That already exists.")

        await self.repo.set_active(user_id, is_active)
        if not is_active:
            # Deactivation revokes in the SAME transaction. Leaving live
            # sessions would mean a deactivated person keeps working until
            # their cookie expires, and `ACCOUNT_DEACTIVATED` is checked per
            # request — but revoking makes it true at the row, not only at the
            # check (`E4-S3`).
            revoked = await self.repo.revoke_sessions(user_id)
        else:
            revoked = 0
        await self.repo.write_audit(
            admin_id=admin.id,
            action="user_deactivated" if not is_active else "user_reactivated",
            target_user_id=user_id, details={"revoked": revoked})
        return {"id": user_id, "is_active": is_active, "revoked": revoked}

    async def set_role(self, admin: Principal, user_id: int, role: str) -> dict:
        target = await self._target(user_id)
        was = target.role
        if was == role:
            return {"id": user_id, "role": role, "revoked": 0}

        if role == "user" and was == "admin":
            if await self.repo.count_active_admins(excluding=user_id) == 0:
                raise ApiError("CONFLICT", field="role", message="That already exists.")

        await self.repo.set_role(user_id, role)

        # DEMOTION revokes; promotion does not (`E4-S4`). A demoted admin's
        # live session carries a token minted while they were one, and the role
        # is read from the row per request — but revoking makes the change
        # immediate rather than merely eventual. A promotion needs no revocation
        # because the new role applies on the very next request anyway, and
        # signing someone out to give them MORE access is gratuitous.
        revoked = await self.repo.revoke_sessions(user_id) if role == "user" else 0

        await self.repo.write_audit(
            admin_id=admin.id, action="role_changed", target_user_id=user_id,
            details={"from": was, "to": role, "revoked": revoked})
        return {"id": user_id, "role": role, "revoked": revoked}

    async def issue_reset(self, admin: Principal, user_id: int) -> dict:
        """`P-ADM-04`. Issues a one-hour token and revokes every session.

        **An admin may not reset another admin, or themselves** (`E4-S4`).
        Admin-on-admin reset is a privilege-escalation path — take over a peer's
        account and you have their audit identity as well as your own; and
        self-reset is the same move with one fewer step.
        """
        from app.modules.auth.service import AccountService

        target = await self._target(user_id)
        # `SW-ADR-098 (3)` and `(4)`, a Fable-5 ruling one tier above this
        # session: peer reset is refused, SELF-reset succeeds. The asymmetry is
        # the point — to reset a peer you demote them first, which is two
        # deliberate, separately audited steps instead of a one-click takeover.
        # An admin resetting themselves takes over nothing they do not have.
        if target.id != admin.id and target.role == "admin":
            raise ApiError("FORBIDDEN")

        token, expires_at = await AccountService(self.db).issue_reset(
            user_id, created_by_admin_id=admin.id)
        revoked = await self.repo.revoke_sessions(user_id)
        await self.repo.write_audit(
            admin_id=admin.id, action="password_reset_issued",
            target_user_id=user_id, details={"revoked": revoked})
        return {"token": token, "expires_at": expires_at}
