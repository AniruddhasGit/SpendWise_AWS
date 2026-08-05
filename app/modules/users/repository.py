"""Queries only. `users` is OUTSIDE row-level security (`SW-ADR-097`), so every
query here carries its own explicit predicate — there is no second layer."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def by_email(self, email: str) -> User | None:
        """Case-insensitive (`SW-ADR-027`). Matches the unique index on
        `lower(email)`, so `Ani@x.com` and `ani@x.com` are one account."""
        return await self.db.scalar(
            select(User).where(func.lower(User.email) == email.strip().lower()))

    async def by_id(self, user_id: int) -> User | None:
        return await self.db.scalar(select(User).where(User.id == user_id))

    async def admin_count(self) -> int:
        return await self.db.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")) or 0

    async def create(self, *, email: str, password_hash: str,
                     display_name: str, role: str) -> User:
        u = User(email=email.strip(), password_hash=password_hash,
                 display_name=display_name.strip(), role=role)
        self.db.add(u)
        await self.db.flush()
        return u
