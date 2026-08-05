"""`auth` module — sign in, sign out, session lifecycle, reset redemption

Owns: **sessions, password_resets**

A module touches only its own tables (`SRC-001 §3.4`). The one sanctioned
crossing is service-to-service, never SQL (`SW-ADR-017`).
"""
