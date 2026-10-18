"""Transparent retry for the one idempotent REPEATABLE READ route.

`GET /api/expenses/summary` runs at REPEATABLE READ so its three aggregates come
from one snapshot (`app/core/db.py`). The cost of that snapshot is SQLSTATE
40001 — 'could not serialize access' — when a concurrent commit invalidates it
mid-read. Postgres documents the only remedy: retry. The read has no side
effects, so replaying it is safe.

`dbapi_error_handler` turns a 40001 into a 503 marked with `RETRYABLE_HEADER`.
This middleware replays the request on that marker and strips it; the client
sees a 200 on success, or the ordinary `INTERNAL` 500 once attempts run out —
never the internal 503.

Pure ASGI, not `BaseHTTPMiddleware`: a BaseHTTP middleware may invoke the app
only once per request (its request body is a one-shot stream), and retrying
means invoking it again. A bodyless GET is safe to replay, so the app is called
with a fresh no-body `receive` on each attempt and the response is buffered
until the outcome is known.
"""
from __future__ import annotations

from starlette.datastructures import Headers

from app.core.db import REPEATABLE_READ_ROUTES
from app.core.errors import RETRYABLE_HEADER, ApiError, envelope

_MAX_ATTEMPTS = 3  # the original try plus two replays

# The opaque 500 a client gets when retries run out — identical to any other
# unhandled failure, pre-serialized so no app code runs to build it.
import json as _json

_INTERNAL = ApiError("INTERNAL")
_INTERNAL_BODY = _json.dumps(envelope(_INTERNAL)).encode()


def _is_retry_route(scope) -> bool:
    # This runs OUTSIDE the router, so scope["route"] is not set yet — match on
    # the request path directly. The summary route takes no path parameters, so
    # its path and its URL path are identical.
    if scope["type"] != "http" or scope.get("method") != "GET":
        return False
    return ("GET", scope.get("path", "")) in REPEATABLE_READ_ROUTES


async def _empty_receive():
    return {"type": "http.request", "body": b"", "more_body": False}


class SerializationRetryMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if not _is_retry_route(scope):
            await self.app(scope, receive, send)
            return

        for attempt in range(_MAX_ATTEMPTS):
            buffered: list[dict] = []
            state = {"retryable": False}

            async def capture(message):
                if message["type"] == "http.response.start":
                    hdrs = Headers(raw=message.get("headers", []))
                    state["retryable"] = hdrs.get(RETRYABLE_HEADER) == "1"
                buffered.append(message)

            await self.app(scope, _empty_receive, capture)

            last = attempt == _MAX_ATTEMPTS - 1
            if not state["retryable"]:
                await _replay(buffered, send)   # success (or a non-retryable error)
                return
            if last:
                await _send_internal_500(send)  # out of retries → opaque 500
                return
            # otherwise: discard the buffered 503 and try again


async def _replay(buffered, send):
    for message in buffered:
        if message["type"] == "http.response.start":
            message = dict(message)
            message["headers"] = [
                (k, v) for (k, v) in message.get("headers", [])
                if k.lower() != RETRYABLE_HEADER.encode()
            ]
        await send(message)


async def _send_internal_500(send):
    await send({
        "type": "http.response.start",
        "status": 500,
        "headers": [
            (b"content-type", b"application/json"),
            (b"cache-control", b"no-store"),
            (b"content-length", str(len(_INTERNAL_BODY)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": _INTERNAL_BODY})
