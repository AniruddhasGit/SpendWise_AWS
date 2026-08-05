"""Serving the built React client from the same container (`SW-ADR-020`).

One image, one service, one deploy, and **no CORS** — the session cookie is
first-party because there is only one party. That decision is what makes
`SameSite=Lax` sufficient and `credentials: 'include'` unnecessary.

Mounted LAST, always. A catch-all registered before the API routers would
swallow every `/api/*` 404 and return `index.html` with a 200 — so a client bug
calling a misspelt endpoint would parse HTML as JSON and report something
unrelated. `main.py` says so at the point of the call, and this module refuses
to mount if `dist/` is absent rather than serving a 404 page nobody wrote.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

log = logging.getLogger("spendwise.spa")

# `app/core/spa.py` -> repository root -> client/dist
DIST = Path(__file__).resolve().parents[2] / "client" / "dist"


def mount(app: FastAPI, dist: Path = DIST) -> bool:
    """Mount the built client. Returns whether anything was mounted.

    A missing `dist/` is NOT an error: `uvicorn app.main:app` during API work is
    a legitimate way to run this, and failing to boot because nobody ran
    `npm run build` would make the backend depend on the frontend toolchain.
    It warns instead, once, naming the command — the same posture `SW-ADR-063`
    takes for a disabled feature.
    """
    index = dist / "index.html"
    if not index.is_file():
        log.warning("client/dist is not built — the API runs, the website does not. "
                    "Run `npm run build` in client/ to serve it from this process.")
        return False

    # Hashed filenames, so a year is safe and a deploy is never stale.
    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str, request: Request):
        # `/api/*` never reaches the catch-all as a 200. Without this, a
        # misspelt endpoint returns index.html and the client parses HTML as
        # JSON — reporting a syntax error at character 0 instead of a 404.
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "NOT_FOUND", "message": "Not found."}},
                headers={"Cache-Control": "no-store"})

        # A real file if there is one (favicon, robots.txt), index.html
        # otherwise — the client owns its own routing.
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_file() and dist in candidate.parents:
            return FileResponse(candidate)

        # NO-STORE on the shell. It names the hashed asset files, so a cached
        # copy of it points at the previous deploy's JavaScript, which is a
        # blank page that clears on a hard refresh and on nothing else.
        return FileResponse(index, headers={"Cache-Control": "no-store"})

    log.info("serving the built client from %s", dist)
    return True
