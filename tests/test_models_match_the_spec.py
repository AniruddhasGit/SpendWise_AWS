"""The ORM models and the generated DDL must describe the same database.

`datamodel.json` is the spec of record and `schema.sql` is generated from it
(`SW-ADR-066`). The ORM models are hand-written — they have to be, because
autogenerating them from the spec would make the spec unreadable and
autogenerating the *migration* from the models would invert the authority.

So they are two descriptions of one thing, and this file is what stops them
drifting. No database required: both sides are read statically.

The failure this prevents is specific and nasty. A column present in the model
and absent from the migration does not fail at import — it fails at the first
query, in production, as a `column does not exist` from a stack frame that does
not mention either file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.core.base import Base

# Importing the models is what registers them on the shared MetaData.
import app.modules.auth.models        # noqa: F401
import app.modules.categories.models  # noqa: F401
import app.modules.expenses.models    # noqa: F401
import app.modules.users.models       # noqa: F401

REPO = Path(__file__).resolve().parents[1]
SPEC = json.loads((REPO / "docs" / "06 DataModel" / "datamodel.json").read_text("utf-8"))
SCHEMA_SQL = (REPO / "docs" / "06 DataModel" / "schema.sql").read_text("utf-8")

# `app_meta` and `admin_audit_log` have no ORM model yet — they belong to
# milestones M4 and beyond. Listed explicitly so the gap is a decision rather
# than an oversight, and so adding one without its model fails here.
NOT_YET_MAPPED = {"app_meta", "admin_audit_log"}


def test_every_spec_table_is_either_mapped_or_explicitly_deferred() -> None:
    spec_tables = set(SPEC["tables"])
    mapped = set(Base.metadata.tables)
    unaccounted = spec_tables - mapped - NOT_YET_MAPPED
    assert not unaccounted, (
        f"tables in the spec with no ORM model and no explicit deferral: "
        f"{sorted(unaccounted)}")


def test_no_model_exists_for_a_table_the_spec_does_not_have() -> None:
    """The other direction. A model with no spec table is a table the migration
    will never create, and a query against it fails at runtime."""
    extra = set(Base.metadata.tables) - set(SPEC["tables"])
    assert not extra, f"models with no table in the spec: {sorted(extra)}"


@pytest.mark.parametrize("table", sorted(set(SPEC["tables"]) - NOT_YET_MAPPED))
def test_columns_match_the_spec_exactly(table: str) -> None:
    """Same names, same order, both directions."""
    spec_cols = [c["name"] for c in SPEC["tables"][table]["columns"]]
    model_cols = [c.name for c in Base.metadata.tables[table].columns]
    assert model_cols == spec_cols, (
        f"{table}: model has {model_cols}, spec has {spec_cols}")


@pytest.mark.parametrize("table", sorted(set(SPEC["tables"]) - NOT_YET_MAPPED))
def test_nullability_matches_the_spec(table: str) -> None:
    """A column nullable in the model and NOT NULL in the migration inserts
    fine in tests and fails on the first real row."""
    for c in SPEC["tables"][table]["columns"]:
        model_col = Base.metadata.tables[table].columns[c["name"]]
        spec_nullable = c["nullability"].upper() != "NOT NULL"
        assert model_col.nullable == spec_nullable, (
            f"{table}.{c['name']}: model nullable={model_col.nullable}, "
            f"spec says {c['nullability']}")


def test_the_composite_foreign_key_exists_and_is_not_set_null() -> None:
    """`SW-ADR-072`. This is what makes a cross-person read achieved through a
    WRITE impossible, and `ON DELETE SET NULL` would break it — it would try to
    null `user_id` too, which is `NOT NULL`."""
    fks = [fk for fk in Base.metadata.tables["expenses"].foreign_key_constraints
           if len(fk.columns) == 2]
    assert len(fks) == 1, "the composite FK on (category_id, user_id) is missing"
    fk = fks[0]
    assert {c.name for c in fk.columns} == {"category_id", "user_id"}
    assert (fk.ondelete or "NO ACTION").upper() in ("NO ACTION", "RESTRICT"), (
        f"ondelete={fk.ondelete!r} — SET NULL would try to null user_id, which is NOT NULL")


def test_money_is_a_bigint_never_numeric_and_never_float() -> None:
    """`CONSTITUTION` Art V.1, asserted against the type rather than trusted."""
    col = Base.metadata.tables["expenses"].columns["amount_paise"]
    assert col.type.__class__.__name__ == "BigInteger"


def test_the_amount_bound_is_in_the_generated_ddl() -> None:
    """`SW-ADR-079` — the cast overflows, not the sum, so the bound is a CHECK."""
    assert "amount_paise > 0 AND amount_paise <= 1000000000000" in SCHEMA_SQL


def test_every_model_check_constraint_appears_in_the_generated_ddl() -> None:
    """The model's CHECKs and the migration's must be the same set. A CHECK only
    in the model is enforced by nothing; only in the migration is a row the ORM
    will happily build and the database will reject."""
    ddl_checks = set(re.findall(r"CONSTRAINT (ck_\w+) CHECK", SCHEMA_SQL))
    for table_name, table in Base.metadata.tables.items():
        if table_name in NOT_YET_MAPPED:
            continue
        for c in table.constraints:
            if c.__class__.__name__ != "CheckConstraint":
                continue
            # `NAMING_CONVENTION` has already expanded `ck_%(table_name)s_%(...)s`
            # by the time the constraint is on the table, so `c.name` is the
            # final identifier. Prefixing again produced
            # `ck_sessions_ck_sessions_user_agent`, which proved the convention
            # is applied rather than proving the constraint is missing.
            name = str(c.name)
            assert name.startswith(f"ck_{table_name}_"), (
                f"{name} does not follow SW-ADR-040's convention — Alembic would "
                f"then generate a different identifier than the migration uses")
            assert name in ddl_checks, (
                f"{name} is on the model and not in schema.sql — enforced by nothing")


def test_users_is_outside_row_level_security_deliberately() -> None:
    """`SW-ADR-097`. Recorded as a test so that turning RLS on for `users` — an
    apparently obvious hardening — fails loudly and points at the reason: login
    must read a row by email BEFORE any verified identity exists."""
    assert SPEC["tables"]["users"]["rls"] is False
    assert SPEC["tables"]["password_resets"]["rls"] is False
    for t in ("expenses", "categories", "sessions"):
        assert SPEC["tables"][t]["rls"] is True
