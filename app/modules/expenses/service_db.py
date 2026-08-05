"""The expenses service — the half that touches the database.

`service.py` holds the pure validation, so it can be tested without one. This
holds the part that needs rows, and it is where `SW-ADR-017`'s sanctioned
crossing actually happens: the repository returns **ids and totals**, and this
service asks the categories **service** for names.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import today
from app.core.errors import ApiError, Violation, validation_error
from app.core.money import to_display
from app.modules.auth.schemas import Principal
from app.modules.categories.service import CategoryService
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.schemas import ExpenseCreate, ExpenseOut, SummaryQuery
from app.modules.expenses.service import elapsed_for, validate_create, validate_summary_query
from app.modules.expenses.summary import CategoryTotal, DayTotal, build_summary


class ExpenseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ExpenseRepository(db)
        self.categories = CategoryService(db)

    async def _to_out(self, principal: Principal, row) -> ExpenseOut:
        names = await self.categories.names_for(principal.id, [row.category_id])
        name = names.get(row.category_id, (None, None))[0] if row.category_id else None
        return ExpenseOut(
            id=row.id, user_id=row.user_id, category_id=row.category_id,
            # NULL when there is no category. `Uncategorised` is a BUCKET label
            # and belongs to the summary alone — on a row it would make a
            # synthetic display string indistinguishable from a real category
            # name (`SW-ADR-141 D`).
            category_name=name,
            amount=to_display(row.amount_paise), amount_paise=row.amount_paise,
            currency=row.currency, description=row.description, spent_on=row.spent_on,
            receipt_key=row.receipt_key, created_at=row.created_at,
            updated_at=row.updated_at,
        )

    async def create(self, principal: Principal, body: ExpenseCreate) -> ExpenseOut:
        paise, description = validate_create(body, as_of=today())
        try:
            # A SAVEPOINT, because the composite FK violation would otherwise
            # abort the REQUEST transaction and the handler could only 500.
            # A second transaction is not an option: it carries no app.user_id
            # and returns zero rows everywhere (`CV-13`, `SW-ADR-144 A`).
            async with self.db.begin_nested():
                row = await self.repo.create(
                    user_id=principal.id, category_id=body.category_id,
                    amount_paise=paise, currency=principal.currency,
                    description=description, spent_on=body.spent_on)
        except IntegrityError as exc:
            if "fk_expenses_category_id_user_id" in str(exc.orig):
                # Person B pointing at person A's category. Refused BY THE
                # DATABASE, not by a pre-read the application could forget —
                # and a pre-read would race (`SW-ADR-072`, `NEG-X-11`).
                raise validation_error([Violation("category.not_owned", "category_id")]) from exc
            raise
        return await self._to_out(principal, row)

    async def get(self, principal: Principal, expense_id: int) -> ExpenseOut:
        row = await self.repo.by_id(principal.id, expense_id)
        if row is None:
            # Identical for not-yours and not-found. Row-level security has
            # ALREADY made another person's row invisible here; this is the
            # second layer, and both must agree on the shape of the refusal.
            raise ApiError("NOT_FOUND")
        return await self._to_out(principal, row)

    async def summary(self, user_id: int, q: SummaryQuery) -> dict:
        validate_summary_query(q)
        elapsed = elapsed_for(q, as_of=today())

        head = await self.repo.headline(user_id, q)
        buckets = await self.repo.by_category(user_id, q)
        days = await self.repo.by_day(user_id, q)
        names = await self.categories.names_for(
            user_id, [b.category_id for b in buckets])

        return build_summary(
            from_=q.from_, to=q.to, elapsed=elapsed,
            headline_total_paise=head[0], headline_count=head[1],
            category_totals=buckets, day_totals=days, names=names,
        )

    # ── the rest of M2 ─────────────────────────────────────────────────────
    #: `SW-ADR-145 A`. A pagination hint, not a rule — the registry holds no
    #: code capable of refusing an over-large one, and inventing one would open
    #: a list `error_codes.md` states is closed.
    LIMIT_MIN, LIMIT_MAX = 1, 200

    async def list_page(self, principal: Principal, *, limit: int, offset: int,
                        from_: date | None, to: date | None,
                        category_id: int | None) -> dict:
        if offset < 0:
            # A 422, because `NEG-X-12` is SEV-1 and the contract wrote
            # `offset.bounds` for it. Here rather than on the annotation so the
            # RULE is right and not merely the field (`SW-ADR-145 B`).
            raise validation_error([Violation("offset.bounds", "offset")])
        if from_ is not None and to is not None and to < from_:
            raise validation_error([Violation("range.order", "to")])

        # CLAMPED, never refused — and echoed back in the body below, so a
        # client that asked for 500 can see it got 200 without counting rows.
        limit = max(self.LIMIT_MIN, min(self.LIMIT_MAX, limit))

        rows, total = await self.repo.list_page(
            principal.id, limit=limit, offset=offset,
            from_=from_, to=to, category_id=category_id)
        # ONE lookup for the whole page, not one per row - the crossing is
        # sanctioned, not free (`SW-ADR-017`).
        names = await self.categories.names_for(
            principal.id, [r.category_id for r in rows])
        items = []
        for r in rows:
            name = names.get(r.category_id, (None, None))[0] if r.category_id else None
            items.append(ExpenseOut(
                id=r.id, user_id=r.user_id, category_id=r.category_id,
                category_name=name, amount=to_display(r.amount_paise),
                amount_paise=r.amount_paise, currency=r.currency,
                description=r.description, spent_on=r.spent_on,
                receipt_key=r.receipt_key, created_at=r.created_at,
                updated_at=r.updated_at))
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def update(self, principal: Principal, expense_id: int, body) -> ExpenseOut:
        from datetime import UTC, datetime
        from app.modules.expenses.service import normalise_description
        from app.core.money import AmountError, parse_amount
        from app.core.clock import spent_on_window

        values: dict = {}
        violations: list[Violation] = []

        if body.amount is not None:
            try:
                values["amount_paise"] = parse_amount(body.amount)
            except AmountError as exc:
                violations.append(Violation(exc.rule, "amount"))
        if body.spent_on is not None:
            floor, ceiling = spent_on_window(today())
            if not (floor <= body.spent_on <= ceiling):
                violations.append(Violation("spent_on.window", "spent_on"))
            else:
                values["spent_on"] = body.spent_on
        if body.description is not None:
            desc = normalise_description(body.description)
            if desc is not None and len(desc) > 500:
                violations.append(Violation("description.length", "description"))
            else:
                values["description"] = desc
        if body.category_id is not None:
            values["category_id"] = body.category_id

        if violations:
            raise validation_error(violations)
        if not values:
            raise validation_error([Violation("field.required", "body")])

        # The service sets it, never a trigger - a trigger would fire on writes
        # that are not edits and make "never edited" unrepresentable (`CV-09`).
        values["updated_at"] = datetime.now(UTC)

        try:
            async with self.db.begin_nested():
                row = await self.repo.update_one(principal.id, expense_id, values)
        except IntegrityError as exc:
            if "fk_expenses_category_id_user_id" in str(exc.orig):
                raise validation_error([Violation("category.not_owned", "category_id")]) from exc
            raise
        if row is None:
            raise ApiError("NOT_FOUND")
        return await self._to_out(principal, row)

    async def delete(self, principal: Principal, expense_id: int) -> None:
        if await self.repo.delete_one(principal.id, expense_id) == 0:
            # Zero rows means not-yours OR not-found, and the refusal is the
            # same either way - row-level security has already made another
            # person's row invisible here.
            raise ApiError("NOT_FOUND")
