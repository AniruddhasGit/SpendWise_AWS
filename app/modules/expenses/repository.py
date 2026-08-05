"""Queries only. Never knows what HTTP is (`SRC-001 §3.3`).

Returns **ids and totals** — never a category name. Names come from the
categories service, which is `SW-ADR-017`'s one sanctioned crossing; a join from
here would be the module-boundary violation `SRC-001 §3.4` forbids.

Every query carries an explicit `user_id` predicate **as well as** relying on
row-level security. Isolation twice (`CONSTITUTION` Art IV.1) — a controller-only
check is the classic false green, and RLS alone would make a missing predicate
invisible until the day someone disables a policy.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, and_, cast, func, literal, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.expenses.models import Expense
from app.modules.expenses.schemas import SummaryQuery
from app.modules.expenses.summary import CategoryTotal, DayTotal


def _filter(q: SummaryQuery):
    """The optional category filter, shared by the queries that re-scope.

    `by_category` deliberately does NOT use it — under a filter the headline
    re-scopes and the breakdown does not, which is what makes the ribbon a
    control rather than a chart (`CV-03`).
    """
    if q.uncategorised:
        return [Expense.category_id.is_(None)]
    if q.category_id is not None:
        return [Expense.category_id == q.category_id]
    return []


class ExpenseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, *, user_id: int, category_id: int | None, amount_paise: int,
                     currency: str, description: str | None, spent_on: date) -> Expense:
        row = Expense(user_id=user_id, category_id=category_id, amount_paise=amount_paise,
                      currency=currency, description=description, spent_on=spent_on)
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def by_id(self, user_id: int, expense_id: int) -> Expense | None:
        return await self.db.scalar(
            select(Expense).where(Expense.user_id == user_id, Expense.id == expense_id))

    async def headline(self, user_id: int, q: SummaryQuery) -> tuple[int, int]:
        """Total and count. The filter APPLIES here.

        `SUM()` over a bigint returns `numeric` in PostgreSQL, which arrives as a
        `Decimal` and would reach the response model. Cast it back (Art V.2).
        """
        stmt = select(
            cast(func.coalesce(func.sum(Expense.amount_paise), 0), BigInteger),
            cast(func.count(), BigInteger),
        ).where(Expense.user_id == user_id,
                Expense.spent_on.between(q.from_, q.to), *_filter(q))
        total, count = (await self.db.execute(stmt)).one()
        return int(total), int(count)

    async def by_category(self, user_id: int, q: SummaryQuery) -> list[CategoryTotal]:
        """Ids and totals only — no join to `categories`. Date-scoped but NOT
        category-scoped: only this one stays whole-period (`CV-03`, `CV-15`)."""
        stmt = (select(Expense.category_id,
                       cast(func.coalesce(func.sum(Expense.amount_paise), 0), BigInteger),
                       cast(func.count(), BigInteger))
                .where(Expense.user_id == user_id, Expense.spent_on.between(q.from_, q.to))
                .group_by(Expense.category_id))
        return [CategoryTotal(cid, int(t), int(n)) for cid, t, n in (await self.db.execute(stmt))]

    async def by_day(self, user_id: int, q: SummaryQuery) -> list[DayTotal]:
        """One row per calendar day, INCLUDING days with no spending.

        Two traps in three lines, both in `GOTCHAS.md`:

        * the owner predicate lives in the **ON** clause. Move it to `WHERE` and
          the LEFT JOIN degenerates to an INNER JOIN, the zero-spend days vanish,
          and **only `SIT-E0-S9-05` notices** — the totals and the average stay
          correct.
        * `COUNT(e.id)`, never `COUNT(*)`. `COUNT(*)` counts the null-extended
          row, so every empty day reports `1`.
        """
        # `literal()` BINDS the value; `literal_column()` would emit the text
        # ":d_from" into the SQL and bind nothing, which is both wrong and the
        # shape of an injection if the value ever came from a request.
        day = func.generate_series(
            literal(q.from_, Date), literal(q.to, Date), text("interval '1 day'"),
        ).table_valued("day").render_derived(name="d", with_types=False)

        stmt = (select(cast(day.c.day, Date),
                       cast(func.coalesce(func.sum(Expense.amount_paise), 0), BigInteger),
                       cast(func.count(Expense.id), BigInteger))
                .select_from(day)
                .outerjoin(Expense, and_(Expense.spent_on == cast(day.c.day, Date),
                                         Expense.user_id == user_id, *_filter(q)))
                .group_by(day.c.day)
                .order_by(day.c.day))
        rows = await self.db.execute(stmt)
        return [DayTotal(d, int(t), int(n)) for d, t, n in rows]

    async def list_page(self, user_id: int, *, limit: int, offset: int,
                        from_: date | None = None, to: date | None = None,
                        category_id: int | None = None) -> tuple[list[Expense], int]:
        """`P-REC-02`. Sorted `spent_on DESC, created_at DESC, id DESC`.

        The tie-breakers are not decoration: two expenses on the same day with
        the same timestamp would otherwise come back in an order the database
        chose, and a page boundary would show a row twice or skip it entirely.
        """
        where = [Expense.user_id == user_id]
        if from_ is not None:
            where.append(Expense.spent_on >= from_)
        if to is not None:
            where.append(Expense.spent_on <= to)
        if category_id is not None:
            where.append(Expense.category_id == category_id)

        total = await self.db.scalar(
            select(func.count()).select_from(Expense).where(*where)) or 0
        rows = await self.db.scalars(
            select(Expense).where(*where)
            .order_by(Expense.spent_on.desc(), Expense.created_at.desc(), Expense.id.desc())
            .limit(limit).offset(offset))
        return list(rows), int(total)

    async def update_one(self, user_id: int, expense_id: int, values: dict) -> Expense | None:
        from sqlalchemy import update as sa_update
        r = await self.db.execute(
            sa_update(Expense)
            .where(Expense.user_id == user_id, Expense.id == expense_id)
            .values(**values).returning(Expense))
        return r.scalar_one_or_none()

    async def delete_one(self, user_id: int, expense_id: int) -> int:
        from sqlalchemy import delete as sa_delete
        r = await self.db.execute(
            sa_delete(Expense).where(Expense.user_id == user_id, Expense.id == expense_id))
        return r.rowcount or 0

    async def null_category(self, user_id: int, category_id: int) -> int:
        """`SRC-001 §7.2`: deleting a category NULLS its expenses.

        Done explicitly, inside the delete transaction, because the composite FK
        is `ON DELETE NO ACTION` — `SET NULL` would try to null `user_id` too,
        which is `NOT NULL` (`SW-ADR-072`).
        """
        from sqlalchemy import update as sa_update
        r = await self.db.execute(
            sa_update(Expense)
            .where(Expense.user_id == user_id, Expense.category_id == category_id)
            .values(category_id=None))
        return r.rowcount or 0

    async def count_in_category(self, user_id: int, category_id: int) -> int:
        return int(await self.db.scalar(
            select(func.count()).select_from(Expense)
            .where(Expense.user_id == user_id, Expense.category_id == category_id)) or 0)
