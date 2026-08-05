"""Password hashing, token minting, and the request identity.

`SW-ADR-136`: the token carries `sub`; `SELECT set_config('app.user_id', :uid, true)`
is the FIRST STATEMENT of the request transaction, with a BOUND PARAMETER - never
`SET LOCAL`, which cannot take one, and interpolating would be the f-string-near-SQL
`SRC-001 §10.3` forbids.

Only then the session lookup: `sessions` is under FORCE ROW LEVEL SECURITY, so the
reverse order returns zero rows for every request ever made.

Built in E0-S5.
"""
from __future__ import annotations
