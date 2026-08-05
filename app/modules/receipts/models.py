"""`receipts.models` — operates on expenses.receipt_key THROUGH the expenses service

The ORM tables this module OWNS. Importing another module's model here is
the boundary violation SRC-001 §3.4 forbids.
"""
from __future__ import annotations

# This module owns NO table (SW-ADR-132). It reaches expenses.receipt_key
# through the expenses SERVICE, never through SQL.
