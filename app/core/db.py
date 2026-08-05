"""The session factory, and the boot assertions that prove isolation is real.

One `AsyncSession` and **one transaction** per request, held on
`request.state.db` (`SW-ADR-144 A`). `set_config('app.user_id', …, true)` is
transaction-local: open a second transaction anywhere and every RLS-protected
query returns **zero rows instead of erroring**. An empty dashboard is
indistinguishable from a person who has spent nothing, which is why this is the
worst failure shape in the system and why the factory raises rather than quietly
handing back a second session.

The isolation level is chosen **at checkout, before `BEGIN`** (`SW-ADR-143 A`,
corrected by `SW-ADR-144 A`). PostgreSQL rejects `SET TRANSACTION ISOLATION
LEVEL` after any query with SQLSTATE `25001`, and `set_config` is the first
statement — so the two APPROVED records can only both hold if the level is set
on the connection.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Literal

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.settings import get_settings

log = logging.getLogger("spendwise.db")

Isolation = Literal["READ COMMITTED", "REPEATABLE READ"]

# Routes whose handler reads the summary's three aggregates and needs them in
# ONE snapshot. Resolved from this table rather than from dependency-resolution
# order, which is what produced two transactions in the first draft.
REPEATABLE_READ_ROUTES: frozenset[tuple[str, str]] = frozenset({
    ("GET", "/api/expenses/summary"),
})

_engine = None


def engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().DATABASE_URL.get_secret_value(),
            # Free tier is db.t4g.micro. Its max_connections is small, and two
            # uvicorn workers each holding a large pool exhausts it long before
            # traffic does (SW-ADR-008's standing cost constraint).
            pool_size=5, max_overflow=2, pool_pre_ping=True, echo=False,
        )
    return _engine


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """The one session for this request. Commits **once**, after the handler
    returns — never a service, never a repository (`CV-12`).

    The create path stitches `category_name` from the categories service AFTER
    the insert; commit inside the service and that read runs outside the
    transaction, returns nothing, and `category_name` silently becomes null.
    """
    async for s in _session_for(request, "READ COMMITTED"):
        yield s


async def get_db_rr(request: Request) -> AsyncIterator[AsyncSession]:
    """`REPEATABLE READ`, for the summary. Declared on the route as
    documentation; the level actually comes from `REPEATABLE_READ_ROUTES`, so it
    cannot depend on which dependency FastAPI resolves first."""
    async for s in _session_for(request, "REPEATABLE READ"):
        yield s


def _wanted_isolation(method: str, path: str) -> Isolation:
    return "REPEATABLE READ" if (method, path) in REPEATABLE_READ_ROUTES else "READ COMMITTED"


async def _session_for(request: Request, declared: Isolation) -> AsyncIterator[AsyncSession]:
    route = request.scope.get("route")
    path = getattr(route, "path", None) or request.url.path
    wanted = _wanted_isolation(request.method, path)

    if declared != wanted:
        # Fail closed and loudly. A mismatch means the route table and the
        # declared dependency disagree, and the silent outcome is a summary
        # whose three aggregates come from three different snapshots.
        raise RuntimeError(
            f"isolation mismatch on {request.method} {path}: the route declares "
            f"{declared} but REPEATABLE_READ_ROUTES says {wanted}"
        )

    if getattr(request.state, "db", None) is not None:
        raise RuntimeError(
            "two session dependencies resolved for one request. There is exactly "
            "one AsyncSession and one transaction per request (SW-ADR-144 A) — a "
            "second one would not carry app.user_id, and every RLS-protected "
            "query in it would return ZERO ROWS rather than erroring."
        )

    conn = await engine().connect()
    conn = await conn.execution_options(isolation_level=wanted)
    sm = async_sessionmaker(bind=conn, expire_on_commit=False)
    async with sm() as session:
        request.state.db = session
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        finally:
            request.state.db = None
            await conn.close()


async def set_request_identity(session: AsyncSession, user_id: int) -> None:
    """The FIRST statement of the request transaction (`SW-ADR-136 B`).

    A **bound parameter**, never `SET LOCAL` — that form cannot take one, and
    interpolating the id would be the f-string-near-SQL `SRC-001 §10.3` forbids.
    """
    await session.execute(
        text("SELECT set_config('app.user_id', :uid, true)"), {"uid": str(user_id)}
    )


# ── the boot assertions (E0-S2 / P-OPS-02) ─────────────────────────────────
PROTECTED = ("expenses", "categories", "sessions")

ASSERTIONS: dict[str, str] = {
    "runtime role is not superuser and cannot bypass RLS":
        "SELECT NOT rolsuper AND NOT rolbypassrls FROM pg_roles WHERE rolname = current_user",
    "runtime role owns no table":
        "SELECT count(*) = 0 FROM pg_class c JOIN pg_roles r ON c.relowner = r.oid "
        "WHERE r.rolname = current_user AND c.relkind = 'r'",
    "FORCE ROW LEVEL SECURITY is on for every protected table":
        "SELECT count(*) = 3 FROM pg_class WHERE relname IN "
        "('expenses','categories','sessions') AND relforcerowsecurity",
    "every protected table has a FOR ALL policy with USING and WITH CHECK":
        "SELECT count(*) = 3 FROM pg_policies WHERE tablename IN "
        "('expenses','categories','sessions') AND cmd = 'ALL' "
        "AND qual IS NOT NULL AND with_check IS NOT NULL",
    "no policy on a money table consults app.is_admin":
        "SELECT count(*) = 0 FROM pg_policies WHERE tablename IN ('expenses','categories') "
        "AND (coalesce(qual,'') LIKE '%is_admin%' OR coalesce(with_check,'') LIKE '%is_admin%')",
}


class StartupAssertionError(RuntimeError):
    """Names the assertion that failed. A boot check that aborts without saying
    which guarantee is missing is a silent failure with extra steps."""


async def assert_isolation_invariants() -> None:
    """Query the catalog and refuse to start if any guarantee is absent.

    **Verified, never assumed** (`CONSTITUTION` Art IV.3). Each has a plausible
    way of being false: a role granted more than intended, a migration run as
    the wrong role, `FORCE` omitted so the owner bypasses its own policies, or
    the admin GUC policy `SW-ADR-129` removed creeping back.

    Both directions matter. `verify_invariants.sql` originally asked only what
    the role *cannot* do and printed all-green against a role with no privileges
    at all — so the grant check is here too (`SW-ADR-137`).
    """
    async with engine().connect() as conn:
        for name, sql in ASSERTIONS.items():
            if not (await conn.execute(text(sql))).scalar():
                raise StartupAssertionError(
                    f"ISOLATION ASSERTION FAILED: {name}. The application will not "
                    f"start. This is the guarantee SRC-001 §4.5 rests on."
                )
        for table in PROTECTED:
            ok = (await conn.execute(
                text("SELECT has_table_privilege(current_user, :t, 'SELECT')"),
                {"t": table})).scalar()
            if not ok:
                raise StartupAssertionError(
                    f"ISOLATION ASSERTION FAILED: the runtime role cannot SELECT "
                    f"{table}. RLS narrows a grant; with no grant it is protecting "
                    f"a door already welded shut (SW-ADR-137)."
                )
    log.info("isolation invariants verified against the catalog: %d checks",
             len(ASSERTIONS) + len(PROTECTED))
