"""`receipts.router` — operates on expenses.receipt_key THROUGH the expenses service

HTTP only: parse, delegate, serialise. **Never writes a query** (SRC-001 §3.3).
"""
from __future__ import annotations
