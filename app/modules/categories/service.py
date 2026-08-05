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

    # ── the rest of M2 ─────────────────────────────────────────────────────
    async def list_for(self, user_id: int):
        return await self.repo.list_for(user_id)

    async def create(self, user_id: int, body):
        from sqlalchemy.exc import IntegrityError
        from app.core.errors import ApiError
        try:
            async with self.repo.db.begin_nested():
                return await self.repo.create_one(user_id, body.name, body.color)
        except IntegrityError as exc:
            # Unique per person, CASE-INSENSITIVELY (`SW-ADR-033`). Enforced by
            # the index, not a pre-read — a pre-read races.
            if "uq_categories_user_id__lower_name" in str(exc.orig):
                # The MESSAGE is the contract's ("That already exists."), not one
                # invented here — `error_codes.messages.by_code` is the spec of
                # record and `test_error_messages_match_the_contract` fails first.
                raise ApiError("CONFLICT", field="name") from exc
            raise

    async def update(self, user_id: int, category_id: int, body):
        from sqlalchemy.exc import IntegrityError
        from app.core.errors import ApiError, Violation, validation_error
        if body.name is None and body.color is None:
            raise validation_error([Violation("field.required", "body")])

        existing = await self.repo.by_id(user_id, category_id)
        if existing is None:
            # 404 for not-yours AND not-found, identically (`P-PRV-03`).
            raise ApiError("NOT_FOUND")

        try:
            async with self.repo.db.begin_nested():
                if body.name is not None:
                    existing.name = body.name
                if body.color is not None:
                    existing.color = body.color
                await self.repo.db.flush()
        except IntegrityError as exc:
            if "uq_categories_user_id__lower_name" in str(exc.orig):
                # The MESSAGE is the contract's ("That already exists."), not one
                # invented here — `error_codes.messages.by_code` is the spec of
                # record and `test_error_messages_match_the_contract` fails first.
                raise ApiError("CONFLICT", field="name") from exc
            raise
        return existing

    async def delete(self, user_id: int, category_id: int) -> int:
        """NULLS the expenses, then deletes the category. Same transaction.

        `SRC-001 §7.2`. Doing it the other way — or relying on a cascade — would
        take someone's spending record with the label, and the record is the
        thing that matters. Returns how many expenses were re-labelled, which is
        the blast radius `SW-ADR-119` wants shown before a destructive confirm.
        """
        from app.core.errors import ApiError
        from app.modules.expenses.repository import ExpenseRepository

        if await self.repo.by_id(user_id, category_id) is None:
            raise ApiError("NOT_FOUND")

        expenses = ExpenseRepository(self.repo.db)
        moved = await expenses.null_category(user_id, category_id)
        await self.repo.delete_one(user_id, category_id)
        return moved
