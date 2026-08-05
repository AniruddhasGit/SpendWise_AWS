"""`receipts` module — operates on expenses.receipt_key THROUGH the expenses service

Owns: **NO TABLE**

A module touches only its own tables (`SRC-001 §3.4`). The one sanctioned
crossing is service-to-service, never SQL (`SW-ADR-017`).
"""
