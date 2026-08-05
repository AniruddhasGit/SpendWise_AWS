"""`expenses` module — the money table - the only module that may write an amount

Owns: **expenses**

A module touches only its own tables (`SRC-001 §3.4`). The one sanctioned
crossing is service-to-service, never SQL (`SW-ADR-017`).
"""
