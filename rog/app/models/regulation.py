from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rog.app.models.base import BaseModel


class Regulation(BaseModel):
    __tablename__ = "regulations"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    authority: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    tags: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    creator = relationship("User")

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    versions = relationship("RegulationVersion", back_populates="regulation", cascade="all,delete-orphan")

