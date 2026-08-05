"""`admin` module — account administration; never reads an amount

Owns: **admin_audit_log**

A module touches only its own tables (`SRC-001 §3.4`). The one sanctioned
crossing is service-to-service, never SQL (`SW-ADR-017`).
"""
