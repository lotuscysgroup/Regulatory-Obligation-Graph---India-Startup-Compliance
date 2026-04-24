"""regulations

Revision ID: 0002_regulations
Revises: 0001_initial
Create Date: 2026-04-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_regulations"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("jurisdiction", sa.String(length=255), nullable=False),
        sa.Column("authority", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_regulations_name", "regulations", ["name"], unique=False)
    op.create_index("ix_regulations_jurisdiction", "regulations", ["jurisdiction"], unique=False)
    op.create_index("ix_regulations_authority", "regulations", ["authority"], unique=False)
    op.create_index("ix_regulations_category", "regulations", ["category"], unique=False)
    op.create_index("ix_regulations_is_deleted", "regulations", ["is_deleted"], unique=False)

    op.create_table(
        "regulation_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("regulation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("file_type", sa.String(length=16), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["regulation_id"], ["regulations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("regulation_id", "version_number", name="uq_regulation_version"),
    )
    op.create_index("ix_regulation_versions_regulation_id", "regulation_versions", ["regulation_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_regulation_versions_regulation_id", table_name="regulation_versions")
    op.drop_table("regulation_versions")

    op.drop_index("ix_regulations_is_deleted", table_name="regulations")
    op.drop_index("ix_regulations_category", table_name="regulations")
    op.drop_index("ix_regulations_authority", table_name="regulations")
    op.drop_index("ix_regulations_jurisdiction", table_name="regulations")
    op.drop_index("ix_regulations_name", table_name="regulations")
    op.drop_table("regulations")

