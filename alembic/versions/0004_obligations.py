"""obligations

Revision ID: 0004_obligations
Revises: 0003_sections
Create Date: 2026-04-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_obligations"
down_revision = "0003_sections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_text", sa.Text(), nullable=False),
        sa.Column("responsible_party", sa.String(length=128), nullable=True),
        sa.Column("deadline_text", sa.String(length=255), nullable=True),
        sa.Column("penalty_text", sa.String(length=255), nullable=True),
        sa.Column("mandatory_flag", sa.Boolean(), nullable=False),
        sa.Column("condition_text", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["section_id"], ["sections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_obligations_section_id", "obligations", ["section_id"], unique=False)
    op.create_index("ix_obligations_mandatory_flag", "obligations", ["mandatory_flag"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_obligations_mandatory_flag", table_name="obligations")
    op.drop_index("ix_obligations_section_id", table_name="obligations")
    op.drop_table("obligations")

