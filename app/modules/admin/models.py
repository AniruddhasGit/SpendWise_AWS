"""`admin.models` — account administration; never reads an amount

The ORM tables this module OWNS. Importing another module's model here is
the boundary violation SRC-001 §3.4 forbids.
"""
from __future__ import annotations

# Tables owned here: admin_audit_log
# Defined in E0-S3 with the baseline migration.
