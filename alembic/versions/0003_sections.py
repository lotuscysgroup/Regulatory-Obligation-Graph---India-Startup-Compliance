"""sections

Revision ID: 0003_sections
Revises: 0002_regulations
Create Date: 2026-04-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_sections"
down_revision = "0002_regulations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("regulation_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section_number", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parent_section_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["regulation_version_id"], ["regulation_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_section_id"], ["sections.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_sections_regulation_version_id", "sections", ["regulation_version_id"], unique=False)
    op.create_index("ix_sections_section_number", "sections", ["section_number"], unique=False)
    op.create_index("ix_sections_parent_section_id", "sections", ["parent_section_id"], unique=False)
    op.create_index("ix_sections_order_index", "sections", ["order_index"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sections_order_index", table_name="sections")
    op.drop_index("ix_sections_parent_section_id", table_name="sections")
    op.drop_index("ix_sections_section_number", table_name="sections")
    op.drop_index("ix_sections_regulation_version_id", table_name="sections")
    op.drop_table("sections")

