"""HTTP only. Parses, delegates, serialises. Never writes a query."""
from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, Db
from app.modules.categories.schemas import CategoryCreate, CategoryOut, CategoryUpdate
from app.modules.categories.service import CategoryService

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(principal: CurrentUser, db: Db) -> list[CategoryOut]:
    return await CategoryService(db).list_for(principal.id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CategoryOut)
async def create(body: CategoryCreate, principal: CurrentUser, db: Db) -> CategoryOut:
    return await CategoryService(db).create(principal.id, body)


@router.patch("/{category_id}", response_model=CategoryOut)
async def update(category_id: int, body: CategoryUpdate,
                 principal: CurrentUser, db: Db) -> CategoryOut:
    return await CategoryService(db).update(principal.id, category_id, body)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(category_id: int, principal: CurrentUser, db: Db) -> Response:
    """Deleting a category NULLS its expenses; it never deletes them
    (`SRC-001 §7.2`). The money is the record — the label is a convenience, and
    losing the record to tidy up the label is the wrong trade."""
    await CategoryService(db).delete(principal.id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
