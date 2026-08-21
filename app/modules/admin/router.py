"""`admin.router` — account administration; never reads an amount.

HTTP only: parse, delegate, serialise. Never writes a query.

**`require_admin` is declared ONCE, on the router**, and `E4-S1` asserts it by
walking FastAPI's route table rather than by listing routes by hand — a
hand-written list is one forgotten line away from an unprotected endpoint, and
the forgetting is silent. `SRC-001 §4.3` says this in the client's own words:
*"One place, not a check copy-pasted into every handler, because I will forget
one."*
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.clock import today
from app.core.deps import CurrentUser, Db, require_admin
from app.modules.admin.schemas import (
    ActiveRequest, AdminOverview, AdminSessionPage, AdminUserPage,
    AdminUserSpending, AuditPage, ResetToken, RoleRequest,
)
from app.modules.admin.service import AdminService
from app.modules.expenses.schemas import require_range

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    # THE one place. Every route below inherits it; a new handler is protected
    # by existing, not by remembering.
    dependencies=[Depends(require_admin)],
)


@router.get("/overview", response_model=AdminOverview)
async def overview(principal: CurrentUser, db: Db) -> AdminOverview:
    """The admin dashboard's figures. Accounts, sessions and actions — never
    money, at any layer (`SRC-001 §4.2`)."""
    return await AdminService(db).overview(principal, today=today())


@router.get("/users", response_model=AdminUserPage)
async def list_users(
    principal: CurrentUser, db: Db,
    limit: Annotated[int, Query()] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(max_length=100)] = None,
    role: Annotated[str | None, Query(pattern="^(user|admin)$")] = None,
    active: Annotated[bool | None, Query()] = None,
    deleted: Annotated[bool | None, Query()] = None,
) -> AdminUserPage:
    """`q` searches email AND display name (`CR-001`: *"search any user with
    their detilas like email id, name"*) — already the behaviour of `_search`.

    **`deleted` defaults to `None`, meaning INCLUDE closed accounts.** Three
    states, not two: `None` everything, `true` only the closed, `false` only the
    live. The default is the one that matters and it is `CR-001 §2`'s — an
    administrator hunting for someone who has left must be able to find them, and
    a default of `false` would hide precisely the accounts the Restore action
    exists for.
    """
    return await AdminService(db).list_users(
        principal, limit=limit, offset=offset, q=q, role=role, active=active,
        deleted=deleted)


@router.get("/users/{user_id}/spending", response_model=AdminUserSpending)
async def user_spending(
    user_id: int, principal: CurrentUser, db: Db,
    # Optional here for the same reason as `GET /api/expenses/summary`, and via
    # the SAME helper — `CR-001 §2` requires these to be one set of rules, not
    # two that agree today.
    from_: Annotated[str | None, Query(alias="from")] = None,
    to: Annotated[str | None, Query()] = None,
) -> AdminUserSpending:
    """`CR-001`, `SW-ADR-151`. One person's total and daily series over a range.

    The capability `SRC-001 §4.2` ruled out and the client reversed in writing.
    It carries money, and it is the ONLY route in this module that does; there is
    no `category_id` parameter and no `by_category` in the response, because the
    same sentence that granted this withheld the categories.

    `from` and `to` are taken as **strings and parsed by `SummaryQuery`**, not
    annotated as `date` — exactly as `GET /api/expenses/summary` does it. A
    `date` annotation would let FastAPI reject a malformed date first, with its
    own error and its own field, and the range rules in `validate_summary_query`
    would never be reached. Same parser, same rules, same refusals as the summary
    the account holder sees of themselves.

    `require_admin` is NOT declared here. It is on the router, once, and `E4-S1`
    walks the route table to prove it — this handler is protected by existing.
    """
    require_range(from_, to)
    return await AdminService(db).spending(principal, user_id, from_, to)


@router.get("/sessions", response_model=AdminSessionPage)
async def list_sessions(
    principal: CurrentUser, db: Db,
    limit: Annotated[int, Query()] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    user_id: Annotated[int | None, Query()] = None,
) -> AdminSessionPage:
    return await AdminService(db).list_sessions(
        principal, limit=limit, offset=offset, user_id=user_id)


@router.get("/audit", response_model=AuditPage)
async def list_audit(
    principal: CurrentUser, db: Db,
    limit: Annotated[int, Query()] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    action: Annotated[str | None, Query(max_length=40)] = None,
    target_user_id: Annotated[int | None, Query()] = None,
) -> AuditPage:
    return await AdminService(db).list_audit(
        principal, limit=limit, offset=offset, action=action,
        target_user_id=target_user_id)


@router.post("/users/{user_id}/revoke-sessions")
async def revoke_sessions(user_id: int, principal: CurrentUser, db: Db) -> dict:
    return await AdminService(db).revoke_sessions(principal, user_id)


@router.post("/users/{user_id}/active")
async def set_active(user_id: int, body: ActiveRequest,
                     principal: CurrentUser, db: Db) -> dict:
    return await AdminService(db).set_active(principal, user_id, body.is_active)


@router.post("/users/{user_id}/role")
async def set_role(user_id: int, body: RoleRequest,
                   principal: CurrentUser, db: Db) -> dict:
    return await AdminService(db).set_role(principal, user_id, body.role)


@router.post("/users/{user_id}/reset", response_model=ResetToken)
async def issue_reset(user_id: int, principal: CurrentUser, db: Db) -> ResetToken:
    """Returns the raw token ONCE. There is no email in this stack
    (`SW-ADR-012`), so the administrator reads it out and hands it over —
    which is why it is never logged and never stored in the clear."""
    return ResetToken(**await AdminService(db).issue_reset(principal, user_id))
