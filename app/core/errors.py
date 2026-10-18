"""One error envelope, one convention, every code testable.

`{"error": {"code", "message", "field"}}`. The code list is **closed** — see
`docs/03 PRD/api/error_codes.md`, generated from `contract.json`. A code not on
it cannot be returned.

`field` carries the **client's** name for the input — `amount`, never
`amount_paise`. FastAPI's default 422 body must never reach a client
(Bible `E1-S7` AC3), so `RequestValidationError` is handled here.

**The tables below are loaded from `contract.json` at import**, not transcribed.
Transcribing them would create a second copy that drifts from the spec of
record, which is the failure `SW-ADR-138` and `SW-ADR-142` were both written
about. If the contract and this module ever disagree, the contract wins — and
`test_errors_match_the_contract.py` fails first.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "03 PRD" / "api" / "contract.json"


@lru_cache(maxsize=1)
def _contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text("utf-8"))


@lru_cache(maxsize=1)
def codes() -> dict[str, int]:
    """`code -> HTTP status`. The closed registry."""
    return {c["code"]: c["status"] for c in _contract()["error_codes"]["codes"]}


@lru_cache(maxsize=1)
def code_messages() -> dict[str, str]:
    """`code -> message`, for the non-validation codes.

    `SESSION_INVALID` has ONE sentence for every cause — expiry, revocation,
    idle timeout, rotated secret, bad signature. Distinguishing them would tell
    an attacker which one they hit.
    """
    return {c["code"]: c["message"]
            for c in _contract()["error_codes"]["messages"]["by_code"]["codes"]}


@lru_cache(maxsize=1)
def rules() -> dict[str, dict]:
    """`rule id -> {field, message}` for the validation rules."""
    return {r["rule"]: r for r in _contract()["error_codes"]["messages"]["rules"]}


@lru_cache(maxsize=1)
def precedence() -> list[str]:
    """The order validation rules are reported in.

    **Short-circuits.** Report the first failure and stop; never collect. Two
    engineers implementing opposite orders would both pass the negative suite,
    because every case there varies exactly one input — the Art IX.3 failure
    `SW-ADR-141` was written to close.
    """
    return list(_contract()["error_codes"]["precedence"]["order"])


@lru_cache(maxsize=1)
def placeholders() -> dict[str, dict]:
    """`field -> {expected, example}`, substituted into `field.type` messages.
    The rendered sentence is what a test asserts on, so the substitution is
    part of the contract, not a presentation detail."""
    ph = _contract()["error_codes"]["messages"]["placeholders"]
    return {t["field"]: t for t in ph["types"]}


@dataclass(frozen=True, slots=True)
class Violation:
    """One broken rule. Ordered by the contract's precedence, not by discovery."""

    rule: str
    field: str | None = None

    @property
    def rank(self) -> int:
        order = precedence()
        return order.index(self.rule) if self.rule in order else len(order)

    def render(self) -> tuple[str, str]:
        """-> `(field, message)`, with placeholders substituted."""
        spec = rules().get(self.rule, {})
        field = self.field or spec.get("field", "")
        message = spec.get("message", "Invalid value.")
        if "{field}" in message or "{expected}" in message:
            ph = placeholders().get(field, {})
            message = (message
                       .replace("{field}", field)
                       .replace("{expected}", ph.get("expected", "a valid value"))
                       .replace("{example}", str(ph.get("example", ""))))
        return field, message


class ApiError(Exception):
    """The only exception that becomes a response body.

    Anything else reaching the handler is a bug and becomes `INTERNAL` with a
    generic message — which never carries detail, an id, or a stack.
    """

    def __init__(self, code: str, *, field: str | None = None, message: str | None = None,
                 headers: dict[str, str] | None = None):
        if code not in codes():
            # A closed list is only closed if the closure is enforced.
            raise ValueError(
                f"{code!r} is not in the error registry. The list in "
                f"docs/03 PRD/api/error_codes.md is CLOSED: an unlisted value is a "
                f"defect, not an extension point."
            )
        super().__init__(code)
        self.code = code
        self.field = field
        self.message = message or code_messages().get(code, "Request failed.")
        # Some codes are only complete WITH a header. `RATE_LIMITED` carries
        # `Retry-After` (`SW-ADR-128`, and the contract's own note says so): a
        # 429 without it tells a client to back off and not for how long, so
        # every client guesses, and the ones that guess short make it worse.
        self.headers = headers or {}

    @property
    def status(self) -> int:
        return codes()[self.code]


def validation_error(violations: list[Violation]) -> ApiError:
    """Pick the winner and build the 422.

    The envelope carries exactly one `field` and one `message`, so when a body
    breaks two rules something has to choose. That something is the contract's
    precedence order, applied here, once — `presence -> type -> value`, then
    fields in the order the request model declares them (`CV-13`/`tie_break`).
    """
    first = min(violations, key=lambda v: v.rank)
    field, message = first.render()
    return ApiError("VALIDATION_ERROR", field=field or None, message=message)


def envelope(err: ApiError) -> dict:
    body: dict[str, object] = {"code": err.code, "message": err.message}
    if err.field:
        body["field"] = err.field
    return {"error": body}


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    # `no-store` first, so a per-code header can never be silently dropped by a
    # dict literal that happened to be written after it.
    return JSONResponse(status_code=exc.status, content=envelope(exc),
                        headers={"Cache-Control": "no-store", **exc.headers})


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """FastAPI's default `{"detail": [...]}` must NEVER reach a client.

    Pydantic *collects* every error; the contract *short-circuits*. So the
    collected errors are mapped to rules, ranked, and only the first is emitted.
    """
    violations: list[Violation] = []
    for e in exc.errors():
        loc = [p for p in e["loc"] if p not in ("body", "query", "path")]
        field = str(loc[0]) if loc else ""
        kind = e["type"]
        if kind in ("missing", "value_error.missing"):
            violations.append(Violation("field.required", field))
        else:
            violations.append(Violation("field.type", field))
    if not violations:                                   # pragma: no cover
        violations = [Violation("field.type", "")]
    return await api_error_handler(_, validation_error(violations))


async def unhandled_handler(_: Request, exc: Exception) -> JSONResponse:
    """Generic by rule. Never a detail, an id, or a stack — those go to the log,
    which is where an operator looks and an attacker does not."""
    return JSONResponse(
        status_code=500,
        content=envelope(ApiError("INTERNAL")),
        headers={"Cache-Control": "no-store"},
    )


# Internal header: `retry_idempotent_serialization` middleware reads it and
# strips it before the response leaves. Never sent to a client.
RETRYABLE_HEADER = "x-serialization-retryable"


def is_serialization_failure(exc: BaseException) -> bool:
    """True when `exc` (or a cause in its chain) is PostgreSQL SQLSTATE 40001 —
    'could not serialize access'. A REPEATABLE READ snapshot that a concurrent
    commit invalidated. Transient by definition: the same read on a fresh
    snapshot succeeds, which is why the only correct response is to retry."""
    seen = 0
    cur: BaseException | None = exc
    while cur is not None and seen < 10:
        code = getattr(cur, "sqlstate", None) or getattr(cur, "pgcode", None)
        if code == "40001" or type(cur).__name__ == "SerializationError":
            return True
        cur = cur.__cause__ or cur.__context__
        seen += 1
    return False


async def dbapi_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """A serialization failure becomes a 503 carrying an internal retry marker.
    The `retry_idempotent_serialization` middleware replays the (idempotent)
    read and strips the marker, so this 503 NEVER reaches a client — on retry
    success it sees 200, and if retries exhaust the middleware returns the same
    opaque `INTERNAL` 500 as any other failure. No new error code is coined, so
    the closed error contract is untouched. Any non-serialization database
    error is the ordinary 500 straight away."""
    if is_serialization_failure(exc):
        return JSONResponse(
            status_code=503,
            content={},  # internal only; the middleware never forwards this body
            headers={"Cache-Control": "no-store", RETRYABLE_HEADER: "1"},
        )
    return await unhandled_handler(request, exc)
