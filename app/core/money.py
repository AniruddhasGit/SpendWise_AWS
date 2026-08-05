"""Integer paise. Never a float, at any point (`CONSTITUTION` Art V.1).

`Decimal` at the boundary, `int` everywhere inside, a display string at render
time only. `SUM()` over a bigint returns `numeric` and arrives as a `Decimal` -
cast it back or one reaches the response model (Art V.2).

Built in E0-S9.
"""
from __future__ import annotations
