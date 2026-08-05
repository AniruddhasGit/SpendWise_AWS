"""One error envelope, one convention, every code testable.

`{"error": {"code", "message", "field"}}`. The code list is CLOSED - see
`docs/03 PRD/api/error_codes.md`, generated from the contract. A code not on it
cannot be returned.

`field` carries the CLIENT's name for the input - `amount`, never `amount_paise`.
FastAPI's default 422 body must never reach a client (Bible E1-S7 AC3).

Built in E0-S5.
"""
from __future__ import annotations
