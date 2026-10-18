"""The application object. Builds the app and includes every router.

Importing this module **validates configuration and aborts non-zero on a missing
required key** — before the port is bound, which is what `E0-S1` AC3 asserts.
That happens as a side effect of importing `app.core.settings`, deliberately:
a loader that only runs inside a lifespan hook has already bound the port by the
time it complains.

One container serves the API and the built React files, with a catch-all route
returning `index.html` (`SW-ADR-020`) — so there is one image, one service, one
deploy, and **no CORS**. The catch-all is mounted LAST, at the bottom of this
file, because it would otherwise swallow every `/api/*` 404.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.core.errors import (
    ApiError, api_error_handler, dbapi_error_handler, unhandled_handler,
    validation_exception_handler,
)
from app.core.health import router as ops_router
from app.core.ratelimit import general_limit_middleware
from app.core.headers import security_headers_middleware
from app.core.retry import SerializationRetryMiddleware
from sqlalchemy.exc import DBAPIError
from app.core.settings import get_settings
from app.core.spa import mount as mount_client
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.expenses.router import router as expenses_router

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
    # The schema is a surface too (F-S3). It was public in every environment
    # because only docs_url was gated; openapi_url defaults to "/openapi.json".
    # Tie it to the same switch as the docs that render it.
    openapi_url="/openapi.json" if settings.LOG_LEVEL == "DEBUG" else None,
)

# ONE envelope for every non-2xx (`SW-ADR-051`). FastAPI's default
# `{"detail": [...]}` must never reach a client (Bible E1-S7 AC3), so
# RequestValidationError is handled rather than left to the framework.
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# Before the generic Exception handler: a serialization failure (SQLSTATE 40001)
# becomes a 503 with an internal retry marker that the retry middleware acts on.
# Registered for the specific class so its response flows back OUT through the
# user middleware (the generic Exception handler runs outside them and could not
# be retried). Everything else still falls to unhandled_handler.
app.add_exception_handler(DBAPIError, dbapi_error_handler)
app.add_exception_handler(Exception, unhandled_handler)

# Transparent serialization retry for the idempotent REPEATABLE READ summary.
# Added FIRST so it is the INNERMOST user middleware — a replay re-runs the read
# (with a fresh session) but NOT the rate limiter above it. Pure ASGI, so it can
# invoke the app more than once; BaseHTTPMiddleware cannot.
app.add_middleware(SerializationRetryMiddleware)

# SW-ADR-128's "everything else" limits. Registered as middleware rather than a
# dependency because it governs every API route including ones not written yet —
# a per-router dependency is a list someone has to remember to extend.
app.middleware("http")(general_limit_middleware)

# Security response headers (F-S1, F-S6). Registered AFTER the limit middleware
# so it is the outermost layer: it stamps headers on every response, including a
# 429 the limiter returns before any route runs.
app.middleware("http")(security_headers_middleware)

app.include_router(ops_router)
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(expenses_router)
app.include_router(admin_router)

# ── LAST ───────────────────────────────────────────────────────────────────
# Everything above this line is a route. Everything below is the fallback. A
# catch-all registered before the API routers matches `/api/anything` first and
# returns index.html with a 200, so a client calling a misspelt endpoint parses
# HTML as JSON and reports a syntax error at character 0 instead of a 404.
#
# Still to come: M5 receipts (deferred — no S3 bucket, prep-queue item 6) ·
# M6 hardening. Each of those goes ABOVE this call.
mount_client(app)
