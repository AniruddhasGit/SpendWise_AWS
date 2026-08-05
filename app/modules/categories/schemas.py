"""Wire shapes for categories. From `contract.json` -> `request_models`."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

STRICT = ConfigDict(extra="ignore", strict=True)

# `^#[0-9a-f]{6}$` — lower-case, six digits, exactly as the CHECK constraint
# spells it. Accepting `#ABC` or `#AABBCC` here and storing it would be refused
# by the database, so the two agree by construction.
Colour = Field(min_length=7, max_length=7, pattern=r"^#[0-9a-f]{6}$")


class CategoryCreate(BaseModel):
    model_config = STRICT
    name: str = Field(min_length=1, max_length=50)
    color: str = Colour


class CategoryUpdate(BaseModel):
    """Rename and recolour (`SW-ADR-114`). Both optional; at least one required,
    checked in the service so the message can name `body`."""
    model_config = STRICT
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, min_length=7, max_length=7,
                              pattern=r"^#[0-9a-f]{6}$")


class CategoryOut(BaseModel):
    id: int
    user_id: int
    name: str
    color: str
    created_at: datetime
