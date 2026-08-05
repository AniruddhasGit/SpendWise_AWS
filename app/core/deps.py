"""FastAPI dependencies: `get_current_user`, `require_admin`.

Written ONCE and applied as `dependencies=[Depends(require_admin)]` on the whole
admin router - one place, never per handler (`SRC-001 §4.3`).

Built in E0-S5.
"""
from __future__ import annotations
