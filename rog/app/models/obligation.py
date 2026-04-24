from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rog.app.models.base import BaseModel


class Obligation(BaseModel):
    __tablename__ = "obligations"

    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_text: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_party: Mapped[str | None] = mapped_column(String(128), nullable=True)
    deadline_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    penalty_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mandatory_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    condition_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    section = relationship("Section", back_populates="obligations")

