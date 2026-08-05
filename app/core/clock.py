"""`today_ist()` behind a dependency - never a library that freezes the
process clock, which would not freeze `now()` inside PostgreSQL (`CV-06`).

Reads `APP_TODAY_OVERRIDE` when set, for the browser-observed gate that an
in-process dependency override cannot reach (`CV-14`, `CV-20`).

Built in E0-S4.
"""
from __future__ import annotations
