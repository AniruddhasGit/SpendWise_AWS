"""The declarative base and the naming convention.

`SW-ADR-040` puts the constraint-naming convention on the `MetaData`, not in the
DDL — so Alembic autogenerates names that match what `generate.py` emits. The
two must agree or a migration will try to drop a constraint by a name the
database does not have.

`docs/06 DataModel/generate.py` reproduces exactly this convention. If you
change one, change both, and `--check` will tell you the moment they disagree.
"""
from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
