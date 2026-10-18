"""Security response headers (F-S1, F-S6).

Registered as one HTTP middleware in `app.main`. Mirrors the shape of
`general_limit_middleware`: a plain `(request, call_next)` coroutine.

Design notes:

* **CSP.** `script-src 'self'` is the one that matters — it closes injected and
  inline script, the real XSS lever. `style-src` keeps `'unsafe-inline'`
  deliberately: the client sets a handful of inline `style=` attributes from
  React (the plot peak's position, the card tilt transform), and React inline
  styles are governed by `style-src`. Inline *style* is a far smaller risk than
  inline *script*, and locking it to `'self'` would break the UI with no real
  security gain. Everything else — fonts, images, connections — is same-origin;
  `data:`/`blob:` images cover inline SVG and canvas.
* **No HSTS.** The deployment has no TLS yet (`SW-ADR-014`, a recorded
  weakness). HSTS over plain HTTP does nothing, so it is omitted rather than
  cargo-culted; it belongs with the TLS work.
* **Cache-Control.** Every `/api/` response is marked `no-store` unless the
  handler already set `Cache-Control` (the error envelope and the SPA shell
  do). Account data — expenses, the export, `/me` — must not sit in a shared or
  browser cache.
* **Server banner.** uvicorn advertises `server: uvicorn`; it names the stack
  for no benefit, so it is removed.
"""
from __future__ import annotations

CSP = "; ".join((
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "connect-src 'self'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "object-src 'none'",
))

PERMISSIONS_POLICY = ", ".join((
    "camera=()", "microphone=()", "geolocation=()",
    "payment=()", "usb=()", "interest-cohort=()",
))

_STATIC_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": PERMISSIONS_POLICY,
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
}


async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    for name, value in _STATIC_HEADERS.items():
        response.headers.setdefault(name, value)
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    # Do not advertise the server stack.
    if "server" in response.headers:
        del response.headers["server"]
    return response
