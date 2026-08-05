"""The eight seeded categories, and name lookup for the sanctioned crossing."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categories.repository import CategoryRepository

CONTRACT = Path(__file__).resolve().parents[3] / "docs" / "03 PRD" / "api" / "contract.json"


@lru_cache(maxsize=1)
def seeded_categories() -> list[tuple[str, str]]:
    """The eight of `SW-ADR-092`, in order, read from the spec of record.

    Not transcribed. The names and colours are ruled, the design system verified
    every contrast figure against them, and a copy here would be a second place
    for them to drift.
    """
    spec = json.loads(CONTRACT.read_text("utf-8"))
    return [(c["name"], c["color"]) for c in spec["categories"]["seeded"]]


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = CategoryRepository(db)

    async def create_defaults(self, user_id: int) -> int:
        """Every new account starts with the eight (`P-REC-05`). Created through
        the same path as any other category, so nothing about them is special
        except that the application made them."""
        made = await self.repo.create_many(user_id, seeded_categories())
        return len(made)

    async def names_for(self, user_id: int, ids: list[int]) -> dict[int, tuple[str, str]]:
        return await self.repo.names_for(user_id, [i for i in ids if i is not None])
