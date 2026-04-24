from __future__ import annotations

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    jurisdiction: str | None = Field(default=None, max_length=255)

