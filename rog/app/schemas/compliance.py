from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    industry: str = Field(min_length=2, max_length=255)
    jurisdiction: str = Field(min_length=2, max_length=255)


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    industry: str
    jurisdiction: str


class ComplianceStatusResponse(BaseModel):
    company_id: uuid.UUID
    obligation_id: uuid.UUID
    status: str
    risk_level: str
    last_checked: datetime


class AlertResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    obligation_id: uuid.UUID
    alert_type: str
    message: str
    due_date: date | None = None
    status: str
    created_at: datetime

