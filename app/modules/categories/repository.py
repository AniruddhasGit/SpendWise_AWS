"""Queries only. `categories` is under RLS, so these are scoped twice: the
explicit `user_id` predicate here, and the policy at the database."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.models import Category


class CategoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_many(self, user_id: int, rows: list[tuple[str, str]]) -> list[Category]:
        made = [Category(user_id=user_id, name=n, color=c) for n, c in rows]
        self.db.add_all(made)
        await self.db.flush()
        return made

    async def list_for(self, user_id: int) -> list[Category]:
        r = await self.db.scalars(
            select(Category).where(Category.user_id == user_id).order_by(Category.id))
        return list(r)

    async def names_for(self, user_id: int, ids: list[int]) -> dict[int, tuple[str, str]]:
        """`id -> (name, colour)`. THE sanctioned crossing (`SW-ADR-017`) is the
        expenses SERVICE calling the categories SERVICE, which calls this — never
        a SQL join from the expenses repository."""
        if not ids:
            return {}
        r = await self.db.scalars(
            select(Category).where(Category.user_id == user_id, Category.id.in_(ids)))
        return {c.id: (c.name, c.color) for c in r}

    async def by_id(self, user_id: int, category_id: int) -> Category | None:
        return await self.db.scalar(
            select(Category).where(Category.user_id == user_id, Category.id == category_id))

    async def create_one(self, user_id: int, name: str, color: str) -> Category:
        c = Category(user_id=user_id, name=name, color=color)
        self.db.add(c)
        await self.db.flush()
        await self.db.refresh(c)
        return c

    async def delete_one(self, user_id: int, category_id: int) -> int:
        """Delete the CATEGORY only. The caller must already have nulled the
        expenses — the composite FK is ON DELETE NO ACTION precisely so this
        cannot silently cascade (`SW-ADR-072`)."""
        from sqlalchemy import delete as sa_delete
        r = await self.db.execute(
            sa_delete(Category).where(Category.user_id == user_id,
                                      Category.id == category_id))
        return r.rowcount or 0
