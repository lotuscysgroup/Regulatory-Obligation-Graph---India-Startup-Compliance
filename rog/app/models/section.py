from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from rog.app.models.base import BaseModel


class Section(BaseModel):
    __tablename__ = "sections"

    regulation_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regulation_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_number: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    regulation_version = relationship("RegulationVersion", back_populates="sections")
    parent = relationship("Section", remote_side="Section.id", back_populates="children")
    children = relationship("Section", back_populates="parent")

