"""obligation relationships

Revision ID: 0005_obligation_relationships
Revises: 0004_obligations
Create Date: 2026-04-24

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_obligation_relationships"
down_revision = "0004_obligations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "obligation_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_obligation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_obligation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["source_obligation_id"], ["obligations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_obligation_id"], ["obligations.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_obligation_relationships_source_obligation_id",
        "obligation_relationships",
        ["source_obligation_id"],
        unique=False,
    )
    op.create_index(
        "ix_obligation_relationships_target_obligation_id",
        "obligation_relationships",
        ["target_obligation_id"],
        unique=False,
    )
    op.create_index(
        "ix_obligation_relationships_relationship_type",
        "obligation_relationships",
        ["relationship_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_obligation_relationships_relationship_type", table_name="obligation_relationships")
    op.drop_index("ix_obligation_relationships_target_obligation_id", table_name="obligation_relationships")
    op.drop_index("ix_obligation_relationships_source_obligation_id", table_name="obligation_relationships")
    op.drop_table("obligation_relationships")

