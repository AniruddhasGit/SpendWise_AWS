"""`expenses.router` — the money table - the only module that may write an amount

HTTP only: parse, delegate, serialise. **Never writes a query** (SRC-001 §3.3).
"""
from __future__ import annotations
