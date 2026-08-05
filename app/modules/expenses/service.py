"""`expenses.service` — the money table - the only module that may write an amount

Translates between HTTP shapes and rows. The ONLY layer permitted to call
another module's service (SW-ADR-017's sanctioned crossing).
"""
from __future__ import annotations
