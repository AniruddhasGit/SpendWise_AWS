"""`auth.models` — sign in, sign out, session lifecycle, reset redemption

The ORM tables this module OWNS. Importing another module's model here is
the boundary violation SRC-001 §3.4 forbids.
"""
from __future__ import annotations

# Tables owned here: sessions, password_resets
# Defined in E0-S3 with the baseline migration.
