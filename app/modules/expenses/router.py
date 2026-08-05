"""HTTP only. Parses, delegates, serialises. Never writes a query."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, CurrentUserRR, Db
from app.modules.expenses.schemas import ExpenseCreate, ExpenseOut, Summary, SummaryQuery
from app.modules.expenses.service_db import ExpenseService

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


# DECLARED BEFORE /{expense_id} — otherwise the literal `summary` is captured by
# the integer path parameter and this endpoint 422s (CV-11). Route order in this
# file is behaviour, not style.
@router.get("/summary", response_model=Summary)
async def summary(
    principal: CurrentUserRR, db: Db,
    from_: Annotated[str, Query(alias="from")],
    to: Annotated[str, Query()],
    category_id: Annotated[int | None, Query()] = None,
    uncategorised: Annotated[bool, Query()] = False,
) -> Summary:
    q = SummaryQuery.model_validate(
        {"from": from_, "to": to, "category_id": category_id,
         "uncategorised": uncategorised})
    return Summary.model_validate(await ExpenseService(db).summary(principal.id, q))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ExpenseOut)
async def create(body: ExpenseCreate, principal: CurrentUser, db: Db) -> ExpenseOut:
    """201, and a forged `user_id` or `id` in the body is DISCARDED rather than
    rejected — a create has no target, so there is nothing to 404 on
    (`SW-ADR-130`, `NEG-X-10`)."""
    return await ExpenseService(db).create(principal, body)


@router.get("/{expense_id}", response_model=ExpenseOut)
async def get_one(expense_id: int, principal: CurrentUser, db: Db) -> ExpenseOut:
    """404 for not-yours AND for not-found, identically. A 403 on an existing
    row and a 404 on a missing one is a working oracle: walk the id space and
    learn which ids are real (`P-PRV-03`)."""
    return await ExpenseService(db).get(principal, expense_id)
