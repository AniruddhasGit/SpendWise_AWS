"""`admin.schemas` — account administration; never reads an amount.

**E4-S2 is enforced here and asserted by introspection**: no model in this file
declares a field capable of holding an amount or a description. That is not a
convention — `test_admin_models_cannot_carry_money` walks these classes and
fails on a field whose name or type could hold one.

`SRC-001 §4.2`, the client's own permission matrix:

> | | user | admin |
> | See anyone else's expense amounts | no | **no** |

The bold **no** is theirs. An admin manages accounts; the money stays private
from everyone, including the person who can deactivate the account holding it.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(extra="ignore", strict=True)


class AdminUser(BaseModel):
    """`P-ADM-01`. Two derived fields and no third.

    `expense_count` and `last_activity` come from `admin_expense_stats()`, a
    `SECURITY DEFINER` function whose `RETURNS TABLE` clause declares exactly
    those two columns (`SW-ADR-129`). "How much" is not answerable from here at
    any layer — not by this model, not by the function, not by a policy.
    """

    id: int
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime
    expense_count: int
    last_activity: date | None


class AdminUserPage(BaseModel):
    items: list[AdminUser]
    total: int
    limit: int
    offset: int


class AdminSession(BaseModel):
    """`P-ADM-02`. **No `ip` and no `user_agent`** (`SW-ADR-106`, `NEG-R-10`).

    "Who is signed in" is an operational question. Answering it does not
    require handing an administrator a location history, and the fields simply
    do not exist on the model — so no handler can leak them by forgetting.
    """

    id: int
    user_id: int
    issued_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class AdminSessionPage(BaseModel):
    items: list[AdminSession]
    total: int
    limit: int
    offset: int


class AuditRow(BaseModel):
    """One audited action.

    `sentence` is rendered SERVER-SIDE (`P-ADM-08`): the audit view shows a
    formatted line, never raw JSON. A client assembling the sentence would
    have to know all nine action types, and would silently print `[object
    Object]` for the tenth.
    """

    id: int
    admin_id: int
    action: str
    target_user_id: int | None
    created_at: datetime
    sentence: str


class AuditPage(BaseModel):
    items: list[AuditRow]
    total: int
    limit: int
    offset: int


class ActiveRequest(BaseModel):
    model_config = STRICT
    is_active: bool


class RoleRequest(BaseModel):
    model_config = STRICT
    role: Literal["user", "admin"]


class ResetToken(BaseModel):
    """`P-ADM-04`. Shown ONCE.

    The database stores only `token_hash`; this is the only moment the token
    exists in the clear anywhere, and it is never logged (`SW-ADR-032`).
    """

    token: str
    expires_at: datetime


class DayCount(BaseModel):
    date: date
    count: int


class AdminOverview(BaseModel):
    """The admin dashboard's headline figures.

    Every number here counts **accounts, sessions or actions**. There is no
    money on this model and there is no way to derive any: `expenses_recorded`
    is a count of rows summed from `admin_expense_stats()`, which returns no
    amount to sum.
    """

    accounts_total: int
    accounts_active: int
    accounts_deactivated: int
    admins: int
    sessions_live: int
    expenses_recorded: int
    accounts_active_last_7_days: int
    accounts_dormant_30_days: int
    accounts_never_used: int
    signups: list[DayCount]
    audit_last_7_days: int
