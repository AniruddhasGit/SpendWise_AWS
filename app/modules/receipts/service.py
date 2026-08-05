"""`receipts.service` — operates on expenses.receipt_key THROUGH the expenses service

Translates between HTTP shapes and rows. The ONLY layer permitted to call
another module's service (SW-ADR-017's sanctioned crossing).
"""
from __future__ import annotations
