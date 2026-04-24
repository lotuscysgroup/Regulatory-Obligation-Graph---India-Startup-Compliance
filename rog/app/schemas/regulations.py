from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class RegulationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    jurisdiction: str = Field(min_length=2, max_length=255)
    authority: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=255)
    tags: dict = Field(default_factory=dict)
    effective_date: date


class RegulationVersionResponse(BaseModel):
    id: uuid.UUID
    version_number: int
    file_path: str
    file_type: str
    effective_date: date
    uploaded_at: datetime


class RegulationResponse(BaseModel):
    id: uuid.UUID
    name: str
    jurisdiction: str
    authority: str
    category: str
    tags: dict
    created_by: uuid.UUID
    created_at: datetime
    is_deleted: bool
    versions: list[RegulationVersionResponse] = []

