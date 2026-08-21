"""HTTP only. Parses, delegates, serialises. Never writes a query."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.core.deps import CurrentUser, CurrentUserRR, Db
from app.modules.expenses.schemas import (
    ExpenseCreate, ExpenseOut, ExpensePage, ExpenseUpdate, Summary, SummaryQuery,
    require_range,
)
from app.modules.expenses.service_db import ExpenseService

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


# DECLARED BEFORE /{expense_id} — otherwise the literal `summary` is captured by
# the integer path parameter and this endpoint 422s (CV-11). Route order in this
# file is behaviour, not style.
@router.get("/summary", response_model=Summary)
async def summary(
    principal: CurrentUserRR, db: Db,
    # OPTIONAL at this layer, deliberately. Annotated as required, FastAPI
    # refuses the request before any rule in this system runs and the caller
    # gets `field.required` — the G2 condition that made `range.required`
    # unreachable. `require_range` reports the missing key with the rule the
    # contract specifies.
    from_: Annotated[str | None, Query(alias="from")] = None,
    to: Annotated[str | None, Query()] = None,
    category_id: Annotated[int | None, Query()] = None,
    uncategorised: Annotated[bool, Query()] = False,
) -> Summary:
    require_range(from_, to)
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


@router.get("", response_model=ExpensePage)
async def list_expenses(
    principal: CurrentUser, db: Db,
    limit: Annotated[int, Query()] = 50,
    offset: Annotated[int, Query()] = 0,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
    category_id: Annotated[int | None, Query()] = None,
) -> ExpensePage:
    """`P-REC-02`.

    NO `ge=`/`le=` on the annotations, deliberately (`SW-ADR-145 B`). FastAPI
    would raise `greater_than_equal`, which the handler maps to `field.type` —
    returning "offset must be an integer, for example 0" for a value that IS an
    integer, when the contract wrote `offset.bounds` for this exact case. The
    annotation carries the TYPE; the service carries the VALUE rule.
    """
    page = await ExpenseService(db).list_page(
        principal, limit=limit, offset=offset, from_=from_, to=to,
        category_id=category_id)
    return ExpensePage.model_validate(page)


@router.patch("/{expense_id}", response_model=ExpenseOut)
async def update(expense_id: int, body: ExpenseUpdate,
                 principal: CurrentUser, db: Db) -> ExpenseOut:
    return await ExpenseService(db).update(principal, expense_id, body)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(expense_id: int, principal: CurrentUser, db: Db) -> Response:
    await ExpenseService(db).delete(principal, expense_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
