"""Queries only. Never knows what HTTP is (`SRC-001 §3.3`)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Session


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, *, user_id: int, expires_at: datetime,
                             user_agent: str | None, ip: str | None) -> Session:
        s = Session(user_id=user_id, expires_at=expires_at,
                    user_agent=(user_agent or "")[:500] or None, ip=ip)
        self.db.add(s)
        await self.db.flush()
        return s

    async def get_session(self, session_id: int) -> Session | None:
        """Readable ONLY after `set_config('app.user_id', ...)` has run.

        `sessions` is under FORCE ROW LEVEL SECURITY, so before the GUC is set
        this returns None for every session that exists (`SW-ADR-136`).
        """
        return await self.db.scalar(select(Session).where(Session.id == session_id))

    async def touch(self, session_id: int, now: datetime) -> None:
        """Bump `last_seen_at`, throttled to once a minute (`SW-ADR-022`)."""
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id,
                   Session.last_seen_at < now.replace(microsecond=0))
            .values(last_seen_at=now))

    async def revoke(self, session_id: int, now: datetime) -> None:
        await self.db.execute(
            update(Session).where(Session.id == session_id,
                                  Session.revoked_at.is_(None))
            .values(revoked_at=now))

    async def revoke_all_for_user(self, user_id: int, now: datetime) -> int:
        r = await self.db.execute(
            update(Session).where(Session.user_id == user_id,
                                  Session.revoked_at.is_(None))
            .values(revoked_at=now))
        return r.rowcount or 0

    async def revoke_all_except(self, user_id: int, keep_session_id: int,
                                now: datetime) -> int:
        """Every live session but the one making the request.

        Signing someone out of the browser they are standing in punishes the
        action this exists to encourage — and "change my password" is exactly
        what a person does when they suspect another session is not theirs.
        """
        r = await self.db.execute(
            update(Session).where(Session.user_id == user_id,
                                  Session.id != keep_session_id,
                                  Session.revoked_at.is_(None))
            .values(revoked_at=now))
        return r.rowcount or 0
