from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rog.app.models.base import BaseModel


class RegulationVersion(BaseModel):
    __tablename__ = "regulation_versions"
    __table_args__ = (
        UniqueConstraint("regulation_id", "version_number", name="uq_regulation_version"),
    )

    regulation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    regulation = relationship("Regulation", back_populates="versions")

