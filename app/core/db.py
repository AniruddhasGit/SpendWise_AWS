"""Session factory, one AsyncSession and ONE transaction per request.

`SW-ADR-144 A`: one factory, held on `request.state.db`. A second call asking for
a different isolation level RAISES rather than silently reusing the wrong one -
because `set_config('app.user_id', ..., true)` is transaction-local, and a second
transaction returns ZERO ROWS rather than erroring. An empty dashboard is
indistinguishable from a person who has spent nothing.

Built in E0-S3.
"""
from __future__ import annotations
