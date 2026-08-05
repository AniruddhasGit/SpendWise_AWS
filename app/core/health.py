"""`/healthz` and `/readyz` — E0-S10, `P-OPS-03`.

**They answer different questions and must not be merged.**

`/healthz` asks *is this process alive*. The container health check calls it,
and a non-200 gets the task killed and replaced. It therefore touches nothing
that can fail for a reason a restart will not fix — in particular not the
database, because a thirty-second RDS blip would otherwise restart a container
that was serving fine, and the restart would take the connection pool with it.

`/readyz` asks *can this process do its job*. It touches the database, reports
the migration revision, and is what a human or a deploy script reads. It is
deliberately NOT wired to anything that kills the task.

The migration revision is read from `alembic_version`, which is the only source
that cannot drift: a constant compiled into the image would report the revision
the image was BUILT with, and `SW-ADR-093` runs migrations at container start,
so those are different questions with the same answer most of the time — which
is the worst kind of wrong.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.settings import get_settings

router = APIRouter(tags=["ops"])


@router.get("/healthz", include_in_schema=False, status_code=status.HTTP_200_OK)
async def healthz() -> Response:
    """200, no body, no database (`P-OPS-03`).

    `Response(status_code=200)` rather than returning `None`: returning None
    from a handler with no response model gives `null` as a JSON body, and
    "bodiless" is the acceptance criterion.
    """
    return Response(status_code=status.HTTP_200_OK, headers={"Cache-Control": "no-store"})


@router.get("/readyz", include_in_schema=False)
async def readyz(db: Annotated[AsyncSession, Depends(get_db)]) -> Response:
    """Status, revision and build.

    503 when the database cannot be reached — a readiness probe that returns
    200 while the database is down has answered the question `/healthz` asks,
    not the one it was asked.
    """
    import json

    settings = get_settings()
    body: dict[str, object] = {
        "status": "ready",
        "revision": None,
        # `EXPOSE_VERSION` is optional and unset by default. `null` is the
        # honest answer when nobody stamped the image; a placeholder like
        # "dev" would be a version string that means "no version string".
        "build": settings.EXPOSE_VERSION,
    }
    code = status.HTTP_200_OK
    try:
        body["revision"] = (await db.execute(
            text("SELECT version_num FROM alembic_version"))).scalar_one_or_none()
    except Exception as exc:                       # noqa: BLE001
        # The TYPE, never the message. A connection error's text carries the
        # host, the port, the database and sometimes the user — and this
        # endpoint is unauthenticated (`SW-ADR-051`'s no-detail rule applies
        # here for the same reason it applies to a 500).
        body["status"] = "not ready"
        body["reason"] = type(exc).__name__
        code = status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(content=json.dumps(body), status_code=code,
                    media_type="application/json",
                    headers={"Cache-Control": "no-store"})
