"""The application object. Builds the app and includes every router.

Importing this module **validates configuration and aborts non-zero on a missing
required key** — before the port is bound, which is what `E0-S1` AC3 asserts.
That happens as a side effect of importing `app.core.settings`, deliberately:
a loader that only runs inside a lifespan hook has already bound the port by the
time it complains.

One container serves the API and the built React files, with a catch-all route
returning `index.html` (`SW-ADR-020`) — so there is one image, one service, one
deploy, and **no CORS**. The catch-all is added in E0-S5; adding it now would
swallow `/api/*` 404s before the routes that produce them exist.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.core.settings import get_settings

# THE CONFIG GATE. Calling this at import means a missing required key aborts
# non-zero here — before uvicorn binds the port, which is what E0-S1 AC3 asserts.
settings = get_settings()

app = FastAPI(
    title="SpendWise",
    version=settings.EXPOSE_VERSION or "unset",
    # The interactive docs are a surface, and surfaces get decided, not defaulted.
    # Left on in development only until a record rules otherwise.
    docs_url="/docs" if settings.LOG_LEVEL == "DEBUG" else None,
    redoc_url=None,
)


@app.get("/healthz", include_in_schema=False)
async def healthz() -> None:
    """`P-OPS-03`: bodiless 200, **without touching the database**.

    The container health check calls this. If it queried the database, a brief
    database blip would restart a container that was serving fine — and the
    restart would take the connection pool with it.
    """
    return None


# Routers are included as their modules are built:
#   E0-S5  auth, users        E0-S6  expenses
#   M2     categories         M3     receipts        M4  admin
