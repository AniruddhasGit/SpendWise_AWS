"""`expenses.repository` — the money table - the only module that may write an amount

Queries only. **Never knows what HTTP is** - no status codes, no request
objects, no exceptions that name a response.
"""
from __future__ import annotations
